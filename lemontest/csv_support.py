'''
Author: Anthony Rodriguez
File: metrics_pgm.py
Created: 11 July 2014
Last Modified: 14 July 2014
'''

import csv
import StringIO

def make_csv(metrics, metrics_type, show_hide):

    output = StringIO.StringIO()

    csv_writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    row = ["ID", "Label", "Upload Time"]

    for column in metrics_type.ordered_columns:
        if show_hide[column[1]] == "true":
            row.append(column[0])

    csv_writer.writerow(row)

    row = []

    for metric in metrics:
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

        csv_writer.writerow(row)
        row = []

    return output.getvalue()