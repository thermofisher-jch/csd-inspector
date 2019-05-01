#!/usr/bin/env python

import os.path

from django.conf import settings

from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_failed,
    print_info,
)


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    raw_trace_path = os.path.join(archive_path, "rawTrace")
    if not os.path.exists(raw_trace_path):
        return print_failed("Could not find rawTrace!")

    message = ""

    for lane in range(1, 5):
        html_file_path = os.path.join(raw_trace_path, "rawTrace_lane_{}.html".format(lane))
        if os.path.exists(html_file_path):
            link_path = (
                settings.MEDIA_URL
                + os.path.relpath(archive_path, settings.MEDIA_ROOT)
                + "/rawTrace/rawTrace_lane_{}.html".format(lane)
            )
            message += " <a target='_blank' href='{}'>Lane {}</a>".format(link_path, lane)

    return print_info(message)
