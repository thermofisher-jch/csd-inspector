#!/usr/bin/env python

import sys
from reports.diagnostics.common.inspector_utils import *
from subprocess import check_call


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        check_call(["./main.sh", archive_path, output_path], cwd=script_dir)
        return print_info("See results for details.")
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
