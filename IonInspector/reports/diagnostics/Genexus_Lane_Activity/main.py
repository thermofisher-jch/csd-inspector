#!/usr/bin/env python

import os
import shutil
from collections import OrderedDict

from IonInspector.reports.diagnostics.common.inspector_utils import (
    read_explog,
    print_info,
    print_failed,
    write_results_from_template,
)


def execute(archive_path, output_path, archive_type):
    try:
        shutil.copy(
            os.path.join(
                archive_path, "CSA/outputs/SigProcActor-00/Bead_density_1000.png"
            ),
            os.path.join(output_path, "Bead_density_1000.png"),
        )
    except IOError:
        return print_failed("Could not find bead density image!")

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

    write_results_from_template(
        {"lanes": lanes}, output_path, os.path.dirname(os.path.realpath(__file__))
    )

    message = " | ".join(["L{} {}".format(k, v[1]) for k, v in lanes.items() if v[0]])
    return print_info(message)
