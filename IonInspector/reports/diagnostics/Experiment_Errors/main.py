#!/usr/bin/env python

import sys
import os
import re
from datetime import datetime

from IonInspector.reports.diagnostics.common.inspector_utils import (
    get_explog_path,
    get_debug_path,
    read_explog,
    handle_exception,
    print_alert,
    print_ok,
    print_failed,
    EXPLOG_FINAL,
    EXPLOG_DATETIME_FORMAT,
    get_debug_log_datetime,
)

DEBUG_ERROR_KEYWORDS = ["ValueError"]


def get_error_lines_in_debug(archive_path, start_time, end_time):
    error_lines = []
    error_pattern = re.compile("|".join(DEBUG_ERROR_KEYWORDS))

    debug_path = get_debug_path(archive_path)
    if not debug_path:
        return error_lines

    with open(debug_path) as dh:
        for line in dh:
            if error_pattern.search(line):
                # this step is time consuming so only done when match is found
                # start_time can be null
                if start_time:
                    out_datetime = get_debug_log_datetime(line=line, start=start_time)
                    # end_time can also be null
                    if end_time and (start_time < out_datetime < end_time):
                        error_lines.append(line)
                    elif start_time < out_datetime:
                        error_lines.append(line)
                else:
                    error_lines.append(line)

    return error_lines


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    results_path = os.path.join(output_path, "results.html")

    try:
        # check the explog name and make sure we are grabbing the right one
        explog_path = get_explog_path(archive_path)
        if os.path.basename(explog_path) != EXPLOG_FINAL:
            print_failed(
                "No explog_final.txt was found so potential errors are not reported."
            )
            return

        # get the explog info
        explog = read_explog(archive_path)
        exp_error_log = explog.get("ExperimentErrorLog", "")

        start_time = None
        if explog.get("Start Time", ""):
            start_time = datetime.strptime(explog["Start Time"], EXPLOG_DATETIME_FORMAT)

        end_time = None
        if explog.get("End Time", ""):
            end_time = datetime.strptime(explog["End Time"], EXPLOG_DATETIME_FORMAT)

        # read debug file
        debug_errors = get_error_lines_in_debug(archive_path, start_time, end_time)

        if exp_error_log or debug_errors:
            with open(results_path, "w") as html_handle:
                html_handle.write(
                    "<html><link rel=stylesheet href=some.css type=text/css>\n"
                )
                html_handle.write("</head><body>")
                html_handle.write('<h2 align="center">Experiment error log</h2>')
                html_handle.write('<p style="text-align:center;">')
                html_handle.write("<table><tbody>")
                html_handle.write("<tr><td colspan=2> ExperimentErrorLog </td></tr>")
                for error in exp_error_log:
                    html_handle.write(
                        "<tr><td> &emsp;&emsp;&emsp;" + str(error) + "</td></tr>"
                    )
                html_handle.write("</tbody></table>")

                html_handle.write('<h2 align="center">debug errors</h2>')
                html_handle.write('<p style="text-align:center;">')
                html_handle.write("<table><tbody>")
                html_handle.write("<tr><td colspan=2> Errors in Debug </td></tr>")
                for error in debug_errors:
                    html_handle.write(
                        "<tr><td> &emsp;&emsp;&emsp;" + str(error) + "</td></tr>"
                    )
                html_handle.write("</tbody></table>")
            return print_alert("Experiment errors found in explog or debug")
        else:
            return print_ok("No experiment or debug errors found")

    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    execute(sys.argv[1], sys.argv[2], sys.argv[3])
