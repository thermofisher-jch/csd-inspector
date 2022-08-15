#!/usr/bin/env python

import os.path

from django.conf import settings

from reports.diagnostics.common.inspector_utils import (
    print_failed,
    print_info,
)


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    auto_cal_path = os.path.join(archive_path, "autoCal")
    if not os.path.exists(auto_cal_path):
        return print_failed("Could not find autoCal!")


    html_file_path = os.path.join(auto_cal_path, "autoCal.html")
    if os.path.exists(html_file_path):
        link_path = (
            settings.MEDIA_URL
            + os.path.relpath(archive_path, settings.MEDIA_ROOT)
            + "/autoCal/autoCal.html"
        )

        os.system("ln -s "+archive_path+ "/autoCal/* "+output_path+"/")
        os.system("ln -s "+archive_path+ "/autoCal/autoCal.html "+output_path+"/results.html")


    return print_info("See results for details.")
