#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    results_path = os.path.join(output_path, "results.html")

    try:
        # check the explog name and make sure we are grabbing the right one
        explog_path = get_explog_path(archive_path)
        if os.path.basename(explog_path) != EXPLOG_FINAL:
            print_failed("No explog_final.txt was found so potential errors are not reported.")
            return

        # get the explog info
        explog = read_explog(archive_path)
        exp_error_log = explog.get("ExperimentErrorLog", "")
        if exp_error_log:
            with open(results_path, 'w') as html_handle:
                html_handle.write("<html><link rel=stylesheet href=some.css type=text/css>\n")
                html_handle.write("</head><body>")
                html_handle.write("<h2 align=\"center\">Experiment error log</h2>")
                html_handle.write("<p style=\"text-align:center;\">")
                html_handle.write("<table><tbody>")
                html_handle.write("<tr><td colspan=2> ExperimentErrorLog </td></tr>")
                for error in exp_error_log:
                    html_handle.write("<tr><td> &emsp;&emsp;&emsp;" + str(error) + "</td></tr>")
                html_handle.write("</tbody></table>")

            print_alert("Experiment errors found in explog")
        else:
            print_ok("No experiment errors found")

    except Exception as exc:
        handle_exception(exc, output_path)


if __name__ == "__main__":
    execute(sys.argv[1], sys.argv[2], sys.argv[3])
