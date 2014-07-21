'''
Author: Anthony Rodriguez
File: metrics_pgm.py
Created: 11 July 2014
Last Modified: 14 July 2014
'''

import csv
import StringIO

def make_csv(metrics, headers):

    output = StringIO.StringIO()

    csv_writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    csv_writer.writerow(headers)

    row = []

    for metric in metrics:
        for column in metric.ordered_columns:
            if column[0] == "Label":
                row.append(metric.archive.label)
            else:
                row.append(metric.get_formatted(column[0]))

        csv_writer.writerow(row)
        row = []

    return output.getvalue()