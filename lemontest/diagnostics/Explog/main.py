#!/usr/bin/env python

import sys
import os
import os.path
from lemontest.diagnostics.common.inspector_utils import *
import csv


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:

        if os.path.exists(os.path.join(archive_path, "explog_final.txt")):
            print_ok("Explog_final.txt was found.")
            return
        if os.path.exists(os.path.join(archive_path, "explog.txt")):
            print_warning("Explog_final.txt was not found but explog.txt was.")
            return

        # if neither of them exist then this is an error condition
        print_alert("Neither explog_final.txt or explog.txt were found.")

    except Exception as exc:
        print_na(str(exc))


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
