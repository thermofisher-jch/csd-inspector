#!/usr/bin/env python

from datetime import datetime
import sys
import os
from lemontest.diagnostics.common.inspector_utils import *

try:
    archive, output = sys.argv[1:3]

    # extract the "mrcoffee" element from the run log
    root = get_xml_from_run_log(archive)
    name_tag = root.find("RunInfo/mrcoffee")
    if name_tag is None:
        raise Exception("Failed to find mrcoffee xml element.")

    # parse the total time into the summary
    total_minutes = int(name_tag.text)
    hours = int(total_minutes / 60)
    minutes = total_minutes % 60
    summary = "No delay." if total_minutes == 0 else "Timer Option Used: "
    if hours:
        summary += "{} Hours ".format(hours)
    if minutes:
        summary += "{} Minutes".format(minutes)

    # get any pause times in the log
    #date_object = None
    #gui_lines = get_lines_from_chef_gui_logs(archive)
    #for gui_line in gui_lines:
    #    if 'Run Paused' in gui_line:
    #        date_string = gui_line.split(':', 1)[1].rsplit(':', 1)[0]
    #        date_object = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S,%f')
    #        break

    print_info(summary)
except Exception as exc:
    print_na(str(exc))
