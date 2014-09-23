
__author__ = 'Anthony Rodriguez'

from lemontest.models import DBSession
from lemontest.models import FileProgress
from lemontest.models import Archive
from lemontest.models import MetricsPGM
from lemontest.models import MetricsProton
from lemontest.models import MetricsOTLog
from lemontest.models import SavedFilters

from pyramid import threadlocal

from celery import task

import os
import csv
import json
import tempfile
import transaction

mapping = {
           'pgm': MetricsPGM,
           'proton': MetricsProton,
           'otlog': MetricsOTLog,
           }

'''
    Task: Creates CSV file of metric data defined by filter
    @param     metric_type:         the type of metric object we are dealing with; pgm, proton, otlog
    @param     file_progress_id:    id of the file progress that keeps track of this csv file status
    @param     filter_id:           id of filter that defines metric data set
    @param     show_hide_string:    json formatted string that holds user defined hidden and shown columns
    @param     sort_by_column:      defines what column to sort metric data set by
'''
@task
def make_csv(metric_type, file_progress_id, filter_id, show_hide_string, sort_by_column):
    '''sets file progress status to running after retrieving it from the DB'''
    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = "Running"
    transaction.commit()

    '''sets the metric type we are working with in this celery task'''
    metric_type = mapping[metric_type]

    '''gets filter object that defines our needed metric data set and sets its file progress relation'''
    filter_obj = DBSession.query(SavedFilters).filter(SavedFilters.id == filter_id).first()
    filter_obj.file_progress_id = file_progress_id
    transaction.commit()

    '''loads show hide dictionary with the user defined hidden and shown metric columns'''
    show_hide = json.loads(show_hide_string)

    '''gets filtered, but unsorted metric data set'''
    metrics_query = filter_obj.get_query()

    '''sorts metric data set'''
    temp = []
    if sort_by_column:
        column, order = sort_by_column.items()[0]
        if column == 'label':
            temp_column = Archive.label
        elif column == 'time':
            temp_column = Archive.time
        elif column in metric_type.columns.values():
            temp_column = getattr(metric_type, column)
        else:
            temp_column = Archive.id

        if order == 'sorting_asc':
            metrics_query = metrics_query.order_by(temp_column.asc())
        elif order == 'sorting_desc':
            metrics_query = metrics_query.order_by(temp_column.desc())
        else:
            metrics_query = metrics_query.order_by(Archive.id.desc())
            column = 'id'

        temp.append(column)
        temp.append(order)
        sort_by_column = temp
    else:
        metrics_query = metrics_query.order_by(Archive.id.desc())
        temp.append("id")
        temp.append("sorting_desc")
        sort_by_column = temp

    '''grabs total size of metric data set for progress updates'''
    total_count = metrics_query.count()
    total_progress = 0
    progress_interval = .01

    '''creates unique temporary file'''
    tempfile.tempdir = threadlocal.get_current_registry().settings['csv_dir']
    fd, name = tempfile.mkstemp('.analysis')
    output = os.fdopen(fd, 'a')

    '''sets the path name of the csv file to its file progress object'''
    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.path = name
    transaction.commit()

    '''BEGIN WRITING TO CSV FILE ON DISK'''
    csv_writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    row = ["ID", "Label", "Upload Time"]

    for column in metric_type.ordered_columns:
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
        '''update progress'''
        total_progress += 1
        if ((total_progress / float(total_count)) >= progress_interval):
            file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
            file_progress_obj.progress = unicode(total_progress / float(total_count))
            transaction.commit()
            progress_interval = (total_progress / float(total_count)) + .01

        csv_writer.writerow(row)
        row = []

    output.close()
    '''END WRITING TO CSV FILE ON DISK'''

    '''sets file progress status to done, and progress to 100%'''
    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress_obj.status = "Done"
    file_progress_obj.progress = unicode(1.00)
    transaction.commit()

    '''if the filter object defining out metric data set was temporary, we delete it'''
    if filter_obj.type == 'temp':
        DBSession.delete(filter_obj)

    '''commit all changes to DB'''
    transaction.commit()