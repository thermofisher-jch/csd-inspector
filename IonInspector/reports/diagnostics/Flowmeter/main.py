#!/usr/bin/env python

import sys
from reports.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        path = os.path.join(archive_path, "onetouch.log")
        with open(path) as log:
            # The first line is not actually part of the CSV, chuck it
            log.readline()
            reader = csv.reader(log)
            headers = reader.next()
            for index, header in enumerate(headers):
                if "Flowmeter0" in header:
                    break
            else:
                return print_alert("Could not find flowmeter column")

            flowmeter_has_non_zero = any([float(l[index]) != 0.0 for l in reader])
            if flowmeter_has_non_zero:
                return print_ok("Flow meter appears to be functioning.")
            else:
                return print_alert("No reading from Flow meter.")

    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    execute(sys.argv[1], sys.argv[2], sys.argv[3])
