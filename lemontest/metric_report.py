import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

import numpy
from scipy import stats

from sqlalchemy import func

from lemontest.views import get_db_queries

from pyramid.httpexceptions import HTTPInternalServerError

from lemontest.models import DBSession
from lemontest.models import FileProgress
from lemontest.models import SavedFilters
from lemontest.models import Graph
from lemontest.models import Archive
from lemontest.models import MetricsPGM
from lemontest.models import MetricsProton
from lemontest.models import MetricsOTLog
from lemontest.models import MetricReport

from celery import task

from pyramid import threadlocal

import time

import os
import json
import tempfile
import transaction

@task
def make_plots(metric_report_id, filter_id):
    reports_cache_dir = threadlocal.get_current_registry().settings['reports_cache_dir']
    report_cache = os.path.join(reports_cache_dir, str(metric_report_id) + '.json')

    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    column = metric_report.metric_column
    metric_type = metric_report.metric_type

    file_progress = FileProgress('report_cache')
    DBSession.add(file_progress)
    file_progress.celery_id = make_plots.request.id
    file_progress.path = report_cache.split('/')[-1]
    DBSession.flush()
    file_progress_id = file_progress.id

    metric_report.data_cache_file_progress = file_progress_id
    metric_report.status = 'Running'
    transaction.commit()

    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    for graph in metric_report.graphs:
        current_graph = DBSession.query(Graph).filter(Graph.id == graph.id).first()
        current_graph.fileprogress.status = 'Running'
        current_graph.fileprogress.celery_id = make_plots.request.id
        transaction.commit()

    metric_object = mapping[metric_type]

    '''get filter object and get query set'''
    filter_obj = DBSession.query(SavedFilters).filter(SavedFilters.id == filter_id).first()
    metrics_query = filter_obj.get_query()

    data = metrics_query.filter(metric_object.get_column(column) != None).values(Archive.id, metric_object.get_column(column))

    max_id = ''

    raw_data = []
    to_cache = []

    for data_point in data:
        if not max_id:
            max_id = data_point[0]
        try:
            raw_data.append(float(data_point[1]))
        except TypeError:
            print type(data_point[1])
        to_cache.append((data_point[0], float(data_point[1])))


    cache_obj = {}
    cache_obj['meta'] = {'metric_type': metric_type, 'metric_column': column, 'metric_report_id': metric_report_id, 'filter_id': filter_id, 'format': '(Archive.id, column values)'}
    cache_obj['data'] = to_cache

    with open(report_cache, 'w') as cache:
        json.dump(cache_obj, cache)

    numpy_data = numpy.array(raw_data)

    db_state = str(len(numpy_data)) + ":" + str(max_id)
    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    metric_report.db_state = db_state
    metric_report.cache_fileprogress.status = "Done"
    transaction.commit()

    report_statistics(metric_report_id, numpy_data)

    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()

    if numpy_data.any():
        for graph in metric_report.graphs:
            name, title, label_x, x_axis_max, x_axis_min, label_y, y_axis_max, y_axis_min = mapping[graph.graph_type](column, numpy_data)

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
            graph.fileprogress.status = 'Error'
            graph.fileprogress.path = 'Error'
            transaction.commit()

    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    metric_report.status = 'Done'
    transaction.commit()

@task
def customize_plots(metric_report_id, filter_id, boxplot_specs, histogram_specs):
    reports_cache_dir = threadlocal.get_current_registry().settings['reports_cache_dir']

    report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    report_cache_path = os.path.join(reports_cache_dir, report.cache_fileprogress.path)

    if report and os.path.exists(report_cache_path):
        metric_column = report.metric_column
        report.status = 'Statistics Available'
        transaction.commit()

        with open(report_cache_path) as cache:
            report_cache = json.load(cache)
    else:
        print "Something went wrong here"
        return HTTPInternalServerError()

    data = [float(i[1]) for i in report_cache['data']]
    numpy_data = numpy.array(data)

    report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()

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
        DBSession.delete(current_graph)
        transaction.commit()

        new_graph = Graph(metric_report_id, graph_type, metric_column, file_progress_id)
        DBSession.add(new_graph)
        transaction.commit()

    report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()

    if numpy_data.any():
        for graph in report.graphs:
            if graph.graph_type == 'boxplot':
                name, title, label_x, x_axis_max, x_axis_min, label_y, y_axis_max, y_axis_min = mapping[graph.graph_type](metric_column, numpy_data, boxplot_specs)
            elif graph.graph_type == 'histogram':
                name, title, label_x, x_axis_max, x_axis_min, label_y, y_axis_max, y_axis_min = mapping[graph.graph_type](metric_column, numpy_data, histogram_specs)

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
            graph.fileprogress.status = 'Error'
            graph.fileprogress.path = 'Error'
            transaction.commit()

    report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    report.status = 'Done'
    transaction.commit()

def report_statistics(metric_report_id, data):
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

def box_plot(column, data, specs=None):
    '''make unique temporary file'''
    tempfile.tempdir = threadlocal.get_current_registry().settings['plots_dir']
    fd, name = tempfile.mkstemp('.png', 'metric_plot')

    if not specs:
        title = column + " (n= " + str(len(data)) + ")"
        y_label = column
    else:
        title = specs['boxplot_title']
        y_label = specs['boxplot_y_axis_label']
        y_bottom = float(specs['boxplot_y_axis_min'])
        y_top = float(specs['boxplot_y_axis_max'])

    '''create instance of a figure'''
    fig = plt.figure()

    axes = fig.gca()
    axes.set_title(title)
    axes.set_ylabel(y_label)

    if column in large_units:
        axes.ticklabel_format(style='sci', axis='y')
        axes.yaxis.major.formatter.set_powerlimits((0,0))

    if specs:
        axes.set_ylim(y_bottom, y_top)

    plt.boxplot(data)

    fig.savefig(name)

    axes = fig.gca()
    x_label = None
    x_axis_min = None
    x_axis_max = None
    y_axis_min, y_axis_max = axes.get_ylim()

    return name, title, x_label, x_axis_max, x_axis_min, y_label, y_axis_max, y_axis_min

def histogram(column, data, specs=None):
    '''make unique temporary file'''
    tempfile.tempdir = threadlocal.get_current_registry().settings['plots_dir']
    fd, name = tempfile.mkstemp('.png', 'metric_plot')

    if not specs:
        title = column + " (n= " + str(len(data)) + ")"
        y_label = 'Quantity'
        x_label = column
    else:
        title = specs['histogram_title']
        y_label = specs['histogram_y_axis_label']
        x_label = specs['histogram_x_axis_label']
        x_left = float(specs['histogram_x_axis_min'])
        x_right = float(specs['histogram_x_axis_max'])
        y_bottom = float(specs['histogram_y_axis_min'])
        y_top = float(specs['histogram_y_axis_max'])

    '''create instance of a figure'''
    fig = plt.figure()

    axes = fig.gca()
    axes.set_title(title)
    axes.set_ylabel(y_label)
    axes.set_xlabel(x_label)

    if column in large_units:
        axes.ticklabel_format(style='sci', axis='x', useOffset=True)
        axes.xaxis.major.formatter.set_powerlimits((0,0))

    if specs:
        axes.set_xlim(x_left, x_right)
        axes.set_ylim(y_bottom, y_top)

    plt.hist(data)

    fig.savefig(name)

    axes = fig.gca()
    x_axis_min, x_axis_max = axes.get_xlim()
    y_axis_min, y_axis_max = axes.get_ylim()

    return name, title, x_label, x_axis_max, x_axis_min, y_label, y_axis_max, y_axis_min

mapping = {
           'pgm': MetricsPGM,
           'proton': MetricsProton,
           'otlog': MetricsOTLog,
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