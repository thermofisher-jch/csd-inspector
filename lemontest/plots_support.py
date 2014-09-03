import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

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

from scipy import stats

import time

import numpy
import tempfile
import transaction

@task
def make_plot(metric_report_id, metric_type, file_progress_id, filter_id, graph_type, column):
    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = "Running"
    transaction.commit()

    metric_object = mapping[metric_type]

    '''get filter object and get query set'''
    filter_obj = DBSession.query(SavedFilters).filter(SavedFilters.id == filter_id).first()
    metrics_query = filter_obj.get_query()

    data_column = metrics_query.values(metric_object.get_column(column))

    temp = []

    for data in data_column:
        try:
            temp.append(float(data[0]))
        except TypeError:
            print type(data[0])
    data_column = numpy.array(temp)

    if data_column.any():
        metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
        metric_report.data_n = len(data_column)
        metric_report.mean = numpy.mean(data_column)
        metric_report.median = numpy.median(data_column)
        metric_report.mode = stats.mode(data_column)[0][0]
        metric_report.q1 = numpy.percentile(data_column, 25)
        metric_report.q3 = numpy.percentile(data_column, 75)
        metric_report.std_dev = numpy.std(data_column)
        metric_report.range_min = data_column.min()
        metric_report.range_max = data_column.max()
        transaction.commit()

        final_status = "Done"

        name = mapping[graph_type](column, data_column)

        graph = Graph(metric_report_id, graph_type, column, file_progress_id)
        DBSession.add(graph)
        transaction.commit()
    else:
        name = ''
        final_status = "Error"

    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = final_status
    file_progress_obj.progress = unicode(1.00)
    file_progress_obj.path = name.split('/')[-1]
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