#!/usr/bin/env python

import json
import os.path

from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_failed,
    print_info,
    write_results_from_template,
)


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    tf_stats_path = os.path.join(
        archive_path, "CSA", "outputs", "BaseCallingActor-00", "TFStats.json"
    )
    if os.path.exists(tf_stats_path):
        with open(tf_stats_path) as fp:
            tf_stats = json.load(fp)
    else:
        return print_failed("Could not find TFStats.json!")

    if "CF-1" in tf_stats:
        histograms = []
        for key in ["Q10", "Q17"]:
            histograms.append(
                {
                    "label": key,
                    "data": [[i, v] for i, v in enumerate(tf_stats["CF-1"][key])],
                }
            )

        write_results_from_template(
            {"histograms": histograms},
            output_path,
            os.path.dirname(os.path.realpath(__file__)),
        )
        return print_info("CF-1 - {0:.1f}%".format(tf_stats["CF-1"].get("Percent 50Q17", "Unknown")))
    else:
        return print_failed("Could not find CF-1 in TFStats.json!")
