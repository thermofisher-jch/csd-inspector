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

    row = []

    for column in metrics_type.ordered_columns:
        if show_hide[column[1]] == "true":
            row.append(column[0])

    csv_writer.writerow(row)

    row = []

    for metric in metrics:
        for column in metric.ordered_columns:
            if show_hide[column[1]] == "true":
                row.append(metric.get_formatted(column[0]))

        csv_writer.writerow(row)
        row = []

    return output.getvalue()