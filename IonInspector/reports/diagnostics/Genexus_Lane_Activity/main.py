#!/usr/bin/env python

from IonInspector.reports.diagnostics.common.inspector_utils import (
    read_explog,
    print_info,
)
from collections import OrderedDict


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

    message = " | ".join(
        ["L{} {}".format(k, v[1]) for k, v in lanes.items() if v[0]]
    )
    return print_info(message)
