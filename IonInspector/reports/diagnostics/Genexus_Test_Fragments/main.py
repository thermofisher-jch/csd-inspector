#!/usr/bin/env python

import json
import os.path

from reports.diagnostics.common.inspector_utils import (
    print_failed,
    print_info,
    write_results_from_template,
)


def get_tf_details(tf_stats, basecaller_stats):
    cf_1 = tf_stats["CF-1"].get("Percent 50Q17", "Unknown")
    total_valid_cf = str(basecaller_stats["BeadSummary"]["tf"].get("valid", "Unknown"))

    if cf_1 == "Unknown":
        return "CF-1: {cf_1} | Total Valid Reads: {total_valid_cf}".format(
            cf_1=cf_1,
            total_valid_cf=total_valid_cf,
        )

    return "CF-1: {cf_1:.1f}% | Total Valid Reads: {total_valid_cf}".format(
        cf_1=cf_1,
        total_valid_cf=total_valid_cf,
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

    basecaller_stats_path = os.path.join(
        archive_path, "CSA", "outputs", "BaseCallingActor-00", "BaseCaller.json"
    )
    if os.path.exists(basecaller_stats_path):
        with open(basecaller_stats_path) as gp:
            basecaller_stats = json.load(gp)
    else:
        return print_failed("Could not find BaseCaller.json")

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

        cf_details = get_tf_details(tf_stats, basecaller_stats)

        return print_info(cf_details)
    else:
        return print_failed("Could not find CF-1 in TFStats.json!")
