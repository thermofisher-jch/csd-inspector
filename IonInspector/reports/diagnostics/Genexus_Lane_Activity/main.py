#!/usr/bin/env python

import os
import shutil
from logging import getLogger
from collections import OrderedDict
from subprocess import check_call

from django.conf import settings

from IonInspector.reports.diagnostics.common.inspector_utils import (
    read_ionstats_basecaller_json,
    read_explog,
    print_info,
    print_failed,
    write_results_from_template,
    get_filePath,
)
from IonInspector.reports.diagnostics.common.inspector_errors import FileNotFoundError
from IonInspector.reports.values import (
    BEAD_DENSITY_FILE_NAME,
    NO_BEAD_IMAGE_FILE,
    NO_BEAD_IMAGE_URL,
    RUN_REPORT_PDF,
)

logger = getLogger(__name__)


def get_total_reads(archive_path, archive_type):
    ionstats = read_ionstats_basecaller_json(archive_path, archive_type)
    total_reads = ionstats["full"]["num_reads"]
    return total_reads


def execute(archive_path, output_path, archive_type):
    total_reads = 0
    active_lanes = -1
    data = read_explog(archive_path)
    lanes = OrderedDict()
    image_messages = []
    bead_messages = []
    try:
        lanes["1"] = (
            data.get("LanesActive1", "no") == "yes",
            data.get("LanesAssay1", "Unknown"),
        )
        lanes["2"] = (
            data.get("LanesActive2", "no") == "yes",
            data.get("LanesAssay2", "Unknown"),
        )
        lanes["3"] = (
            data.get("LanesActive3", "no") == "yes",
            data.get("LanesAssay3", "Unknown"),
        )
        lanes["4"] = (
            data.get("LanesActive4", "no") == "yes",
            data.get("LanesAssay4", "Unknown"),
        )

        total_reads = get_total_reads(archive_path, archive_type)
        active_lanes = [active for active, assay in lanes.values()].count(True)

        # copy images from lane diagnostics
        for lane_number, lane_info in lanes.items():
            enabled, assay_name = lane_info
            if enabled:
                for filename in {
                    "multilane_plot_lane_{}_aligned_rl_histogram.png".format(
                        lane_number
                    ),
                    "multilane_plot_lane_{}_q20_rl_histogram.png".format(lane_number),
                }:
                    try:
                        shutil.copy(
                            os.path.join(archive_path, "Lane_Diagnostics/" + filename),
                            os.path.join(output_path, filename),
                        )
                    except IOError:
                        image_messages.append("Could not find '{}'".format(filename))
    except FileNotFoundError as err:
        logger.error(err.file_path)
        image_messages.append("Could not find '{}'".format(err.file_path))
    finally:
        # copy bead density
        bead_image_path = os.path.join(output_path, BEAD_DENSITY_FILE_NAME)
        bead_image_url = NO_BEAD_IMAGE_URL
        try:
            bead_image_found = get_filePath(archive_path, BEAD_DENSITY_FILE_NAME)
            if bead_image_found is None:
                report_pdf_path = os.path.join(archive_path, RUN_REPORT_PDF)
                if os.path.exists(report_pdf_path):
                    extract_util = [
                        "./IonInspector/reports/diagnostics/Genexus_Lane_Activity/extract_bead_density.sh",
                        output_path,
                    ]
                    check_call(extract_util)
                if os.path.exists(bead_image_path):
                    bead_image_found = bead_image_path
                else:
                    bead_messages.append("Could not find bead density image!")
        except IOError as err:
            bead_image_found = None
            bead_messages.append(
                "I/O Error accessing bead density image: " + err.message
            )
        if bead_image_found is None:
            os.symlink(NO_BEAD_IMAGE_FILE, bead_image_path)
        else:
            bead_image_url = settings.MEDIA_URL + os.path.relpath(
                bead_image_path, settings.MEDIA_ROOT
            )
            if bead_image_found != bead_image_path:
                os.symlink(bead_image_found, bead_image_path)

    # write template
    if active_lanes > 0:
        write_results_from_template(
            {
                "lanes": lanes,
                "bead_image_url": bead_image_url,
                "total_reads": total_reads,
                "active_lanes": active_lanes,
                "average_reads_per_lane": total_reads / active_lanes,
            },
            output_path,
            os.path.dirname(os.path.realpath(__file__)),
        )

    messages = bead_messages + [
        "<strong>L{}</strong> {}".format(k, v[1]) for k, v in lanes.items() if v[0]
    ]

    # summary message and result code
    if len(image_messages) > 0:
        if len(image_messages) > 1:
            messages.append(
                "Could not find {} diagnostic images".format(str(len(image_messages)))
            )
        else:
            messages.extend(image_messages)
    message = "<br>".join(messages)
    if active_lanes <= 0 or len(bead_messages) > 0:
        return print_failed(message)
    return print_info(message)
