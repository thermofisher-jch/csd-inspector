#!/usr/bin/env python

from IonInspector.reports.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    explog = read_explog(archive_path)
    run_type = explog.get("RunType", "Unknown")
    return print_info("Run Type: {}".format(run_type))



