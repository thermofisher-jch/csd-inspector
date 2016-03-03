
__author__ = 'Anthony Rodriguez'

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

import numpy
from scipy import stats

from pyramid.httpexceptions import HTTPInternalServerError

from lemontest.models import DBSession
from lemontest.models import FileProgress
from lemontest.models import SavedFilters
from lemontest.models import Graph
from lemontest.models import Archive
from lemontest.models import MetricReport

from celery import task

from pyramid import threadlocal

import os
import json
import tempfile
import transaction

'''
    Task: Generates two graphs for each Metric Report. One boxplot, and one Histogram
    @param     metric_report_id:    id of metric report we are creating plots for
    @param     filter_id:           id of filter object that defines metric data set
'''
@task
def make_plots(metric_report_id, filter_id):
    '''gets path to store report cache'''
    '''creates .json file to cache metric data set'''
    reports_cache_dir = threadlocal.get_current_registry().settings['reports_cache_dir']
    report_cache = os.path.join(reports_cache_dir, str(metric_report_id) + '.json')

    '''gets metric report from DB, and report data needed'''
    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    column = metric_report.metric_column
    metric_type = metric_report.metric_type

    '''creates new file progress for the report cache we write to disk. Sets celery id and path'''
    file_progress = FileProgress('report_cache')
    DBSession.add(file_progress)
    file_progress.celery_id = make_plots.request.id
    file_progress.path = report_cache.split('/')[-1]
    DBSession.flush()
    file_progress_id = file_progress.id

    '''link relation to file progress, and set status to running'''
    metric_report.data_cache_file_progress = file_progress_id
    metric_report.status = 'Running'
    transaction.commit()

    '''for each graph, set status to running and set celery task id'''
    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    for graph in metric_report.graphs:
        current_graph = DBSession.query(Graph).filter(Graph.id == graph.id).first()
        current_graph.fileprogress.status = 'Running'
        current_graph.fileprogress.celery_id = make_plots.request.id
        transaction.commit()

    '''get metric object that we are using for this celery task'''
    metric_object = mapping[metric_type]

    '''get filter object and get query set'''
    filter_obj = DBSession.query(SavedFilters).filter(SavedFilters.id == filter_id).first()
    metrics_query = filter_obj.get_query()

    '''order metric data set so that first entry is entry with highest id'''
    metrics_query = metrics_query.order_by(Archive.id.desc())

    '''the variable data holds all of the values of specified column to graph'''
    data = metrics_query.filter(metric_object.get_column(column) != None).values(Archive.id, metric_object.get_column(column))

    max_id = ''

    raw_data = []
    to_cache = []

    '''sorts out NoneTypes from the data set that cannot be converted to float type numbers'''
    for data_point in data:
        '''grab first data point's archive id'''
        '''this id will be the highest id in the data set'''
        if not max_id:
            max_id = data_point[0]
        try:
            raw_data.append(float(data_point[1]))
        except TypeError:
            '''Type that could not be converted to float was found'''
            pass
        to_cache.append((data_point[0], float(data_point[1])))

    '''create dictionary to be written to disk that contains filtered data set to plot, and pertinent data'''
    cache_obj = {}
    cache_obj['meta'] = {'metric_type': metric_type, 'metric_column': column, 'metric_report_id': metric_report_id, 'filter_id': filter_id, 'format': '(Archive.id, column values)'}
    cache_obj['data'] = to_cache

    '''write metric data set to disk'''
    with open(report_cache, 'w') as cache:
        json.dump(cache_obj, cache)

    '''create numpy array of data set for statistical analysis'''
    numpy_data = numpy.array(raw_data)

    '''set DB state variable to report and set cache file progress object status to done'''
    db_state = str(len(numpy_data)) + ":" + str(max_id)
    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    metric_report.db_state = db_state
    metric_report.cache_fileprogress.status = "Done"
    transaction.commit()

    '''call to function that sets report statistics'''
    report_statistics(metric_report_id, numpy_data)

    '''refresh metric report object with what is in the DB'''
    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()

    '''if there is any statistical data to be plotted, we create one of each type of graph'''
    '''else we set the file progress objects of each graph to error'''
    if numpy_data.any():
        for graph in metric_report.graphs:
            name, title, label_x, x_axis_max, x_axis_min, label_y, y_axis_max, y_axis_min = mapping[graph.graph_type](column, numpy_data)

            '''set graph properties'''
            current_graph = DBSession.query(Graph).filter(Graph.id == graph.id).first()
            current_graph.fileprogress.status = 'Done'
            current_graph.fileprogress.path = name.split('/')[-1]
            current_graph.title = title
            current_graph.label_x = label_x
            current_graph.label_y = label_y
            current_graph.x_axis_min = x_axis_min
            current_graph.x_axis_max = x_axis_max
            current_graph.y_axis_min = y_axis_min
            current_graph.y_axis_max = y_axis_max
            transaction.commit()
    else:
        for graph in metric_report.graphs:
            current_graph = DBSession.query(Graph).filter(Graph.id == graph.id).first()
            current_graph.fileprogress.status = 'Error'
            current_graph.fileprogress.path = 'Error'
            transaction.commit()

    '''set metric report status to done and commit all pending changes to DB'''
    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    metric_report.status = 'Done'
    transaction.commit()

'''
    Task: Customizes the already created graphs of the report
    @param    metric_report_id:     id of metric report
    @param    filter_id:            if of filter that defines metric data set
    @param    boxplot_specs:        custom specifications for the boxplot
    @param    histogram_specs:        custom specifications for the histogram
'''
@task
def customize_plots(metric_report_id, filter_id, boxplot_specs, histogram_specs):
    '''get directory that has report caches'''
    reports_cache_dir = threadlocal.get_current_registry().settings['reports_cache_dir']
    plots_dir = threadlocal.get_current_registry().settings['plots_dir']

    '''get report from DB'''
    report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    report_cache_path = os.path.join(reports_cache_dir, report.cache_fileprogress.path)

    '''make sure report and report data cache exists'''
    '''if report and cache both exist, set report status to Statistics Available, because those have not changed'''
    '''else return some Internal Server Error'''
    '''I'm not sure if an error will ever happen here, but checking nevertheless'''
    if report and os.path.exists(report_cache_path):
        metric_column = report.metric_column
        report.status = 'Statistics Available'
        transaction.commit()

        with open(report_cache_path) as cache:
            report_cache = json.load(cache)
    else:
        print "Something went wrong here"
        return HTTPInternalServerError()

    '''get data from data cache, and store that data in a numpy array for analysis'''
    data = [float(i[1]) for i in report_cache['data']]
    numpy_data = numpy.array(data)

    '''refresh report from DB'''
    report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()

    current_boxplot_specs = {}
    current_histogram_specs = {}
    '''for each graph in report, delete old graphs and create new empty graphs'''
    for graph in report.graphs:
        '''create file_progress object to track file progress'''
        file_progress = FileProgress('plot')
        DBSession.add(file_progress)
        file_progress.celery_id = make_plots.request.id
        DBSession.flush()
        file_progress_id = file_progress.id
        transaction.commit()

        '''delete old file_progress associated with graphs'''
        current_graph = DBSession.query(Graph).filter(Graph.id == graph.id).first()
        graph_type = current_graph.graph_type
        if graph_type == 'boxplot':
            current_boxplot_specs = current_graph.get_specs()
        elif graph_type == 'histogram':
            current_histogram_specs = current_graph.get_specs()
        to_delete = os.path.join(plots_dir, current_graph.fileprogress.path)
        if os.path.exists(to_delete):
            os.remove(to_delete)
        DBSession.delete(current_graph)
        transaction.commit()

        new_graph = Graph(metric_report_id, graph_type, metric_column, file_progress_id)
        DBSession.add(new_graph)
        transaction.commit()

    '''refresh report from DB'''
    report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()

    '''if there is data to analyze, for each newly created a graph create plot with user specifications'''
    '''else set file progress to error for each graph'''
    if numpy_data.any():
        for graph in report.graphs:
            '''if there is a change for each graph type we change it'''
            '''else we keep the specs the same as the previous graph'''
            if graph.graph_type == 'boxplot':
                if boxplot_specs:
                    name, title, label_x, x_axis_max, x_axis_min, label_y, y_axis_max, y_axis_min = mapping[graph.graph_type](metric_column, numpy_data, boxplot_specs)
                else:
                    name, title, label_x, x_axis_max, x_axis_min, label_y, y_axis_max, y_axis_min = mapping[graph.graph_type](metric_column, numpy_data, current_boxplot_specs)
            elif graph.graph_type == 'histogram':
                if histogram_specs:
                    name, title, label_x, x_axis_max, x_axis_min, label_y, y_axis_max, y_axis_min = mapping[graph.graph_type](metric_column, numpy_data, histogram_specs)
                else:
                    name, title, label_x, x_axis_max, x_axis_min, label_y, y_axis_max, y_axis_min = mapping[graph.graph_type](metric_column, numpy_data, current_histogram_specs)

            current_graph = DBSession.query(Graph).filter(Graph.id == graph.id).first()
            current_graph.fileprogress.status = 'Done'
            current_graph.fileprogress.path = name.split('/')[-1]
            current_graph.title = title
            current_graph.label_x = label_x
            current_graph.label_y = label_y
            current_graph.x_axis_min = x_axis_min
            current_graph.x_axis_max = x_axis_max
            current_graph.y_axis_min = y_axis_min
            current_graph.y_axis_max = y_axis_max
            transaction.commit()
    else:
        for graph in report.graphs:
            current_graph = DBSession.query(Graph).filter(Graph.id == graph.id).first()
            current_graph.fileprogress.status = 'Error'
            current_graph.fileprogress.path = 'Error'
            transaction.commit()
    '''set report status to done and commit any pending changes to DB'''
    report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    report.status = 'Done'
    transaction.commit()

'''
    Task: calculate statistics based on metric data set
    @param    metric_report_id:    id of metric report
    @param    data:                the numpy array stored metric data set
'''
def report_statistics(metric_report_id, data):
    '''calculate and set statistics for report, set status to Statistics Available once they are done, commit changes to DB'''
    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    metric_report.data_n = len(data)
    metric_report.mean = numpy.mean(data)
    metric_report.median = numpy.median(data)
    metric_report.mode = stats.mode(data)[0][0]
    metric_report.q1 = numpy.percentile(data, 25)
    metric_report.q3 = numpy.percentile(data, 75)
    metric_report.std_dev = numpy.std(data)
    metric_report.range_min = data.min()
    metric_report.range_max = data.max()
    metric_report.status = 'Statistics Available'
    transaction.commit()

def make_plot_file():
    tempfile.tempdir = threadlocal.get_current_registry().settings['plots_dir']
    fd, name = tempfile.mkstemp('.png', 'metric_plot_')
    os.fchmod(fd, 0644)
    return name

'''
    Task: create boxplot with given metric data set
    @param    column:      the column we are plotting
    @param    data:        the data we are plotting
    @param    specs:       user specifications (optional, default = None)
'''
def box_plot(column, data, specs=None):
    '''make unique temporary file in plots directory'''
    name = make_plot_file()

    '''if specs is not set, we use default title and y-axis label'''
    '''else we check if that parameter exists in specs, and if so set it'''
    '''else we set it to default'''
    if not specs:
        title = column + " (n= " + str(len(data)) + ")"
        y_label = column
    else:
        if 'boxplot_title' not in specs or not specs['boxplot_title']:
            title = column + " (n= " + str(len(data)) + ")"
        else:
            title = specs['boxplot_title']

        if 'boxplot_label_y' not in specs or not specs['boxplot_label_y']:
            y_label = column
        else:
            y_label = specs['boxplot_label_y']

        if 'boxplot_y_axis_min' in specs and specs['boxplot_y_axis_min']:
            y_bottom = float(specs['boxplot_y_axis_min'])
        else:
            y_bottom = ''

        if 'boxplot_y_axis_max' in specs and specs['boxplot_y_axis_max']:
            y_top = float(specs['boxplot_y_axis_max'])
        else:
            y_top = ''

    '''create instance of a figure'''
    fig = plt.figure()

    '''get instances of axes from the figure'''
    axes = fig.gca()
    axes.set_title(title)
    axes.set_ylabel(y_label)

    '''if the column is part of the defined large columns, we use scientific notation to keep the graph clean looking'''
    if column in large_units:
        axes.ticklabel_format(style='sci', axis='y')
        axes.yaxis.major.formatter.set_powerlimits((0,0))

    '''if there are specified y limits, we set them'''
    if specs:
        if y_bottom and y_top:
            axes.set_ylim(y_bottom, y_top)
        elif y_bottom:
            axes.set_ylim(bottom=y_bottom)
        elif y_top:
            axes.set_ylim(top=y_top)

    '''create plot'''
    plt.boxplot(data)

    '''save figure to disk in defined plots directory'''
    fig.savefig(name)

    '''grab/set current specification to store in DB graph object'''
    '''x-axis specs are all None because it is a boxplot'''
    axes = fig.gca()
    x_label = None
    x_axis_min = None
    x_axis_max = None
    y_axis_min, y_axis_max = axes.get_ylim()

    return name, title, x_label, x_axis_max, x_axis_min, y_label, y_axis_max, y_axis_min

'''
    Task: create histogram with given metric data set
    @param    column:      the column we are plotting
    @param    data:        the data we are plotting
    @param    specs:       user specifications (optional, default = None)
'''
def histogram(column, data, specs=None):
    '''make unique temporary file in plots directory'''
    name = make_plot_file()

    '''if specs is not set, we use default title, x-axis label, and y-axis label'''
    '''else we check if that parameter exists in specs, and if so set it'''
    '''else we set it to default'''
    if not specs:
        title = column + " (n= " + str(len(data)) + ")"
        y_label = 'No. of Runs'
        x_label = column
    else:
        if 'histogram_title' not in specs or not specs['histogram_title']:
            title = column + " (n= " + str(len(data)) + ")"
        else:
            title = specs['histogram_title']

        if 'histogram_label_y' not in specs or not specs['histogram_label_y']:
            y_label = 'Quantity'
        else:
            y_label = specs['histogram_label_y']

        if 'histogram_label_x' not in specs or not specs['histogram_label_x']:
            x_label = column
        else:
            x_label = specs['histogram_label_x']

        if 'histogram_x_axis_min' in specs and specs['histogram_x_axis_min']:
            x_left = float(specs['histogram_x_axis_min'])
        else:
            x_left = ''

        if 'histogram_x_axis_max' in specs and specs['histogram_x_axis_max']:
            x_right = float(specs['histogram_x_axis_max'])
        else:
            x_right = ''

        if 'histogram_y_axis_min' in specs and specs['histogram_y_axis_min']:
            y_bottom = float(specs['histogram_y_axis_min'])
        else:
            y_bottom = ''

        if 'histogram_y_axis_max' in specs and specs['histogram_y_axis_max']:
            y_top = float(specs['histogram_y_axis_max'])
        else:
            y_top = ''

    '''create instance of a figure'''
    fig = plt.figure()

    '''get instances of axes from the figure'''
    axes = fig.gca()
    axes.set_title(title)
    axes.set_ylabel(y_label)
    axes.set_xlabel(x_label)

    '''if the column is part of the defined large columns, we use scientific notation to keep the graph clean looking'''
    if column in large_units:
        axes.ticklabel_format(style='sci', axis='x', useOffset=True)
        axes.xaxis.major.formatter.set_powerlimits((0,0))

    '''create plot'''
    n, bins, patches = plt.hist(data)

    y_top_default = max(n)

    axes.set_ylim(top=(y_top_default + 4))

    '''if there are specified x or y limits, we set them'''
    if specs:
        if x_left and x_right:
            axes.set_xlim(x_left, x_right)
        elif x_left:
            axes.set_xlim(left=x_left)
        elif x_right:
            axes.set_xlim(right=x_right)

        if y_bottom and y_top:
            axes.set_ylim(y_bottom, y_top)
        elif y_bottom:
            axes.set_ylim(bottom=y_bottom)
        elif y_top:
            axes.set_ylim(top=y_top)

    '''save figure to disk in defined plots directory'''
    fig.savefig(name)

    '''grab current specification to store in DB graph object'''
    axes = fig.gca()
    x_axis_min, x_axis_max = axes.get_xlim()
    y_axis_min, y_axis_max = axes.get_ylim()

    return name, title, x_label, x_axis_max, x_axis_min, y_label, y_axis_max, y_axis_min

mapping = {
           'boxplot': box_plot,
           'histogram': histogram
           }

large_units = [
               'ISP Wells',
               'Live Wells',
               'Test Fragment',
               'Lib Wells',
               'Polyclonal',
               'Primer Dimer',
               'Low Quality',
               'Usable Reads',
               'Cycles',
               'Flows',
               'Total Bases',
               'Total Reads',
               ]