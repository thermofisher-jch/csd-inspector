#!/usr/bin/env python

import sys
from IonInspector.reports.diagnostics.common.inspector_utils import *
from subprocess import check_call


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        check_call(['./main.sh', archive_path, output_path])
    except Exception as exc:
        return print_na(str(exc))

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
