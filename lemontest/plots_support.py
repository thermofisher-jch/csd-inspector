import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

import numpy
from scipy import stats

from sqlalchemy import func

from lemontest.views import get_db_queries

from lemontest.models import DBSession
from lemontest.models import FileProgress
from lemontest.models import SavedFilters
from lemontest.models import Graph
from lemontest.models import MetricsPGM
from lemontest.models import MetricsProton
from lemontest.models import MetricsOTLog
from lemontest.models import MetricReport

from celery import task

from pyramid import threadlocal

import time

import tempfile
import transaction

@task
def make_plots(metric_report_id, filter_id):
    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    column = metric_report.metric_column
    metric_type = metric_report.metric_type
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
    max_id = filter_obj.max_archive_id


    data = metrics_query.filter(metric_object.get_column(column) != None).values(metric_object.get_column(column))

    raw_data = []

    for data_point in data:
        try:
            raw_data.append(float(data_point[0]))
        except TypeError:
            print type(data_point[0])
    numpy_data = numpy.array(raw_data)

    db_state = str(len(numpy_data)) + ":" + str(max_id)
    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    metric_report.db_state = db_state
    transaction.commit()

    report_statistics(metric_report_id, numpy_data)

    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()

    if numpy_data.any():
        for graph in metric_report.graphs:
            name = mapping[graph.graph_type](column, numpy_data)

            current_graph = DBSession.query(Graph).filter(Graph.id == graph.id).first()
            current_graph.fileprogress.status = 'Done'
            current_graph.fileprogress.path = name.split('/')[-1]
            transaction.commit()
    else:
        for graph in metric_report.graphs:
            graph.fileprogress.status = 'Error'
            graph.fileprogress.path = 'Error'
            transaction.commit()

    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    metric_report.status = 'Done'
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

def box_plot(column, data):
    '''make unique temporary file'''
    tempfile.tempdir = threadlocal.get_current_registry().settings['plots_dir']
    fd, name = tempfile.mkstemp('.png', 'metric_plot')

    '''create instance of a figure'''
    fig = plt.figure()

    axes = fig.gca()
    axes.set_ylabel(column)
    axes.set_title(column + " (n= " + str(len(data)) + ")")

    plt.boxplot(data)

    fig.savefig(name)

    return name

def histogram(column, data):
    '''make unique temporary file'''
    tempfile.tempdir = threadlocal.get_current_registry().settings['plots_dir']
    fd, name = tempfile.mkstemp('.png', 'metric_plot')

    '''create instance of a figure'''
    fig = plt.figure()

    axes = fig.gca()
    axes.set_xlabel(column)
    axes.set_ylabel('Quantity')
    axes.set_title(column + " (n= " + str(len(data)) + ")")

    plt.hist(data)

    fig.savefig(name)

    return name

mapping = {
           'pgm': MetricsPGM,
           'proton': MetricsProton,
           'otlog': MetricsOTLog,
           'boxplot': box_plot,
           'histogram': histogram
           }