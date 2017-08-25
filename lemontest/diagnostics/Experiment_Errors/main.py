#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *

archive_path, output_path = sys.argv[1:3]
results_path = os.path.join(output_path, "results.html")

try:
    # get the explog info
    explog = read_explog(archive_path)
    expErrorLog = explog.get("ExperimentErrorLog", "")
    if expErrorLog:
        with open(results_path, 'w') as html_handle:
            html_handle.write("<html><link rel=stylesheet href=some.css type=text/css>\n")
            html_handle.write("</head><body>")
            html_handle.write("<h2 align=\"center\">Experiment error log</h2>")
            html_handle.write("<p style=\"text-align:center;\">")

            html_handle.write("<table><tbody>")
            print_alert("Experiment errors found in explog")
            html_handle.write("<tr><td colspan=2> ExperimentErrorLog </td></tr>")
            for error in expErrorLog:
                html_handle.write("<tr><td> &emsp;&emsp;&emsp;" + str(error) + "</td></tr>")
            html_handle.write("</tbody></table>")
    else:
        print_ok("No experiment errors found")

except Exception as exc:
    handle_exception(exc, output_path)


