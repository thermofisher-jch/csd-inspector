import matplotlib
from decimal import Decimal
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from lemontest.views import get_db_queries

from lemontest.models import DBSession
from lemontest.models import FileProgress

from lemontest.models import MetricsPGM
from lemontest.models import MetricsProton
from lemontest.models import MetricsOTLog

from lemontest.models import Saved_Filters_PGM
from lemontest.models import Saved_Filters_Proton
from lemontest.models import Saved_Filters_OTLog

from celery import task

import os
import csv
import json
import tempfile
import transaction
import decimal

mapping = {
           'pgm': (MetricsPGM, Saved_Filters_PGM),
           'proton': (MetricsProton, Saved_Filters_Proton),
           'otlog': (MetricsOTLog, Saved_Filters_OTLog),
           }

@task
def make_plot(metric_type, file_progress_id, filter_id, graph_type ,column):
    '''BEGIN INITIAL SETUP'''
    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = "Running"
    transaction.commit()

    metric_object = mapping[metric_type][0]

    filter_type = mapping[metric_type][1]
    '''END INITIAL SETUP'''

    '''get filter object and get query set'''
    filter_obj = DBSession.query(filter_type).filter(filter_type.id == filter_id).first()
    metrics_query = filter_obj.get_query()

    data_column = metrics_query.values(metric_object.get_column(column))

    temp = []

    for data in data_column:
        try:
            temp.append(float(data[0]))
        except TypeError:
            print type(data[0])
    data_column = temp

    if graph_type == 'boxplot':
        name = box_plot(column, data_column)
    elif graph_type == 'histogram':
        name = histogram(column, data_column)

    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = "Done"
    file_progress_obj.progress = unicode(1.00)
    file_progress_obj.path = name.split('/')[-1]
    transaction.commit()

    if filter_obj.type == 'temp':
        DBSession.delete(filter_obj)

    transaction.commit()

def box_plot(column, data):
    '''Calculate for progress, might be removed later
    total_count = metrics_query.count()
    total_progress = 0
    progress_interval = .01'''

    '''make unique temporary file'''
    tempfile.tempdir = '/tmp/plots'
    fd, name = tempfile.mkstemp('.png', 'metric_plot')
    save_dir = '/home/rodriga/inspector/lemontest/static/img/plots/'

    '''create instance of a figure'''
    fig = plt.figure()

    axes = fig.gca()
    axes.set_xlabel('x label')
    axes.set_ylabel('y label')
    axes.set_title(column)

    plt.boxplot(data)

    fig.savefig(save_dir + name.split('/')[-1])

    return name

def histogram(column, data):
    '''make unique temporary file'''
    tempfile.tempdir = '/tmp/plots'
    fd, name = tempfile.mkstemp('.png', 'metric_plot')
    save_dir = '/home/rodriga/inspector/lemontest/static/img/plots/'

    '''create instance of a figure'''
    fig = plt.figure()

    axes = fig.gca()
    axes.set_xlabel('x label')
    axes.set_ylabel('y label')
    axes.set_title(column)

    plt.hist(data)

    fig.savefig(save_dir + name.split('/')[-1])

    return name