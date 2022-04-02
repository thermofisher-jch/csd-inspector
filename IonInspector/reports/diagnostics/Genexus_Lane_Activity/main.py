#!/usr/bin/env python

import os
import logging
import shutil
from collections import OrderedDict
from django.conf import settings

from IonInspector.reports.diagnostics.common.inspector_utils import (
    read_ionstats_basecaller_json,
    read_explog,
    print_info,
    print_failed,
    write_results_from_template,
    get_filePath,
)
from IonInspector.reports.values import (
    BEAD_DENSITY_FILE_NAME,
    NO_BEAD_IMAGE_FILE,
    NO_BEAD_IMAGE_URL,
)

# NO_BEAD_IMAGE_URL = "static/img/no-bead-density-found.png"
# NO_BEAD_IMAGE_FILE = os.path.normpath(
# os.path.join(
# os.path.dirname(
# os.path.realpath(__file__)
# ),
# "../../../" + NO_BEAD_IMAGE_URL
# )
# )

logger = logging.getLogger(__name__)


def get_total_reads(archive_path, archive_type):
    ionstats = read_ionstats_basecaller_json(archive_path, archive_type)
    total_reads = ionstats["full"]["num_reads"]
    return total_reads


def execute(archive_path, output_path, archive_type):
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
    finally:
        # copy bead density
        bead_image_path = os.path.join(output_path, BEAD_DENSITY_FILE_NAME)
        bead_image_url = NO_BEAD_IMAGE_URL
        try:
            bead_image_found = get_filePath(archive_path, BEAD_DENSITY_FILE_NAME)
            if bead_image_found is None:
                bead_messages.append("Could not find bead density image!")
                os.symlink(NO_BEAD_IMAGE_FILE, bead_image_path)
            else:
                bead_image_url = settings.MEDIA_URL + os.path.relpath(
                    bead_image_path, settings.MEDIA_ROOT
                )
                os.symlink(bead_image_found, bead_image_path)
        except IOError as err:
            bead_messages.append(
                "I/O Error accessing bead density image: " + err.message
            )
            bead_image_url = NO_BEAD_IMAGE_URL
            os.symlink(NO_BEAD_IMAGE_FILE, bead_image_path)

    # write template
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
    # image_messages
    if len(image_messages) > 0:
        if len(image_messages) > 1:
            messages.append(
                "Could not find {} diagnostic images".format(str(len(image_messages)))
            )
        else:
            messages.extend(image_messages)
    message = "<br>".join(messages)
    if len(bead_messages) > 0:
        return print_failed(message)
    return print_info(message)
