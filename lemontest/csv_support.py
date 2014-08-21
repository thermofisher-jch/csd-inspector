'''
Author: Anthony Rodriguez
File: metrics_pgm.py
Created: 11 July 2014
Last Modified: 14 July 2014
'''
from lemontest.views import get_db_queries
from lemontest.models import DBSession
from lemontest.models import FileProgress

from celery import task

import os
import csv
import json
import tempfile
import transaction

@task
def make_csv(metrics_type, filter_type, file_progress_id, show_hide_string, filter_id=None, request=None):
    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = "Running"
    transaction.commit()

    if filter_id:
        filter_obj = DBSession.query(filter_type).filter(filter_type.id == filter_id).first()
    elif request:
        filter_obj, saved_filters, extra_params = get_db_queries(request, metrics_type)
        filter_obj.type = "temp"
        DBSession.add(filter_obj)
        DBSession.flush()

    filter_obj.file_progress_id = file_progress_id
    transaction.commit()

    show_hide = json.loads(show_hide_string)

    metrics_query = filter_obj.get_query()

    total_count = metrics_query.count()
    total_progress = 0
    progress_interval = .01

    tempfile.tempdir = '/tmp/'
    fd, name = tempfile.mkstemp('.analysis')
    output = os.fdopen(fd, 'a')

    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.path = name
    transaction.commit()

    csv_writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    row = ["ID", "Label", "Upload Time"]

    for column in metrics_type.ordered_columns:
        if show_hide[column[1]] == "true":
            row.append(column[0])

    csv_writer.writerow(row)

    row = []

    for metric in metrics_query:
        row.append(metric.archive.id)
        row.append((metric.archive.label).encode('UTF-8'))
        row.append(metric.archive.time)
        for column in metric.ordered_columns:
            if show_hide[column[1]] == "true":
                row_entry = metric.get_value(column[0])
                if isinstance(row_entry, unicode):
                    row_entry = row_entry.encode('UTF-8')
                    row.append(row_entry)
                else:
                    row.append(row_entry)
        total_progress += 1
        if ((total_progress / float(total_count)) >= progress_interval):
            file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
            file_progress_obj.progress = unicode(total_progress / float(total_count))
            transaction.commit()
            progress_interval = (total_progress / float(total_count)) + .01

        csv_writer.writerow(row)
        row = []

    output.close()

    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = "Done"
    file_progress_obj.progress = unicode(1.00)
    file_progress_obj.path = name
    transaction.commit()

    if filter_obj.type == 'temp':
        DBSession.delete(filter_obj)

    transaction.commit()