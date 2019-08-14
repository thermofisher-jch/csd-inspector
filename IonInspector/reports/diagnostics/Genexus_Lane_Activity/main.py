#!/usr/bin/env python

import os
import shutil
from collections import OrderedDict
from django.conf import settings

from IonInspector.reports.diagnostics.common.inspector_utils import (
    read_explog,
    print_info,
    print_failed,
    write_results_from_template,
)


def execute(archive_path, output_path, archive_type):
    data = read_explog(archive_path)
    lanes = OrderedDict()
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

    # copy bead density
    bead_image_path = os.path.join(output_path, "Bead_density_1000.png")
    bead_image_url = "/media/" + os.path.relpath(bead_image_path, settings.MEDIA_ROOT)
    try:
        shutil.copy(
            os.path.join(
                archive_path, "CSA/outputs/SigProcActor-00/Bead_density_1000.png"
            ),
            bead_image_path,
        )
    except IOError:
        bead_image_url = None
        return print_failed("Could not find bead density image!")

    # copy images from lane diagnostics
    for lane_number, lane_info in lanes.items():
        enabled, assay_name = lane_info
        if enabled:
            for filename in {
                "multilane_plot_lane_{}_aligned_rl_histogram.png".format(lane_number),
                "multilane_plot_lane_{}_q20_rl_histogram.png".format(lane_number),
            }:
                try:
                    shutil.copy(
                        os.path.join(archive_path, "Lane_Diagnostics/" + filename),
                        os.path.join(output_path, filename),
                    )
                except IOError:
                    return print_failed("Could not find lane diagnostics image '{}'!".format(filename))

    # write template
    write_results_from_template(
        {"lanes": lanes, "bead_image_url": bead_image_url}, output_path, os.path.dirname(os.path.realpath(__file__))
    )

    message = " <br> ".join(["<strong>L{}</strong> {}".format(k, v[1]) for k, v in lanes.items() if v[0]])
    return print_info(message)
