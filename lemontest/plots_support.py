import matplotlib
matplotlib.use('Agg')

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

from pylab import *
import os
import csv
import json
import tempfile
import transaction

mapping = {
           'pgm': (MetricsPGM, Saved_Filters_PGM),
           'proton': (MetricsProton, Saved_Filters_Proton),
           'otlog': (MetricsOTLog, Saved_Filters_OTLog)
           }

@task
def box_plot(metric_type, file_progress_id, filter_id, column):

    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = "Running"
    transaction.commit()

    filter_type = mapping[metric_type][1]

    filter_obj = DBSession.query(filter_type).filter(filter_type.id == filter_id).first()

    filter_obj.file_progress_id = file_progress_id
    transaction.commit()

    metrics_query = filter_obj.get_query()

    total_count = metrics_query.count()
    total_progress = 0
    progress_interval = .01

    tempfile.tempdir = '/tmp/plots'
    fd, name = tempfile.mkstemp('.png', 'metric_plot')
    output = os.fdopen(fd, 'a')

    save_dir = '/home/rodriga/inspector/lemontest/static/img/plots/'

    savefig(save_dir + name.split('/')[-1])

    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = "Done"
    file_progress_obj.progress = unicode(1.00)
    file_progress_obj.path = name.split('/')[-1]
    transaction.commit()

    if filter_obj.type == 'temp':
        DBSession.delete(filter_obj)

    transaction.commit()