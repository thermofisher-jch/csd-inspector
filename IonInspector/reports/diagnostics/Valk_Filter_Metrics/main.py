#!/usr/bin/env python

import os
import sys
import json
import ConfigParser

from IonInspector.reports.diagnostics.common.inspector_utils import (
    write_results_from_template,
    print_info,
    print_warning,
)


def parse_sigproc_stats(archive_path):
    stats = {}
    config = ConfigParser.RawConfigParser()
    config.read(
        os.path.join(
            archive_path, "CSA", "outputs", "SigProcActor-00", "analysis.bfmask.stats"
        )
    )
    for name, value in config.items("global"):
        stats[name] = float(value)
    return stats


def parse_base_caller_stats(archive_path):
    with open(
        os.path.join(
            archive_path, "CSA", "outputs", "BaseCallingActor-00", "BaseCaller.json"
        )
    ) as fp:
        stats = json.load(fp)
    return stats["Filtering"]["ReadDetails"]["lib"]


def check_total_wells(data):
    if "value" in data:
        return data["value"]
    elif "children" in data:
        return sum([check_total_wells(c) for c in data["children"]])
    else:
        raise ValueError("Child must have value or children!")


def execute(archive_path, output_path, archive_type):
    sigproc_stats = parse_sigproc_stats(archive_path)
    base_caller_stats = parse_base_caller_stats(archive_path)
    data = {
        "name": "Wells",
        "color": "#d3e2ff",
        "children": [
            {
                "name": "Beads",
                "color": "#bad1ff",
                "children": [
                    {"name": "Duds", "value": sigproc_stats["dud beads"]},
                    {
                        "name": "Test Fragment",
                        "value": sigproc_stats["test fragment beads"],
                    },
                    {
                        "name": "Library",
                        "color": "#9ebeff",
                        "children": [
                            {
                                "name": "Final Library Wells",
                                "color": "#7aa6ff",
                                "value": base_caller_stats["valid"],
                            },
                            {
                                "name": "Polyclonal",
                                "value": base_caller_stats["bkgmodel_polyclonal"],
                            },
                            {
                                "name": "Primer Dimer",
                                "value": base_caller_stats["adapter_trim"],
                            },
                            {
                                "name": "Quality Filter",
                                "value": base_caller_stats["quality_filter"],
                            },
                            {
                                "name": "Low Quality: High PPF",
                                "color": "#a5a5a5",
                                "value": base_caller_stats["bkgmodel_high_ppf"],
                            },
                            {
                                "name": "Low Quality: Bad Key",
                                "color": "#a5a5a5",
                                "value": base_caller_stats["bkgmodel_keypass"],
                            },
                            {
                                "name": "Low Quality: Short Read",
                                "color": "#a5a5a5",
                                "value": base_caller_stats["short"],
                            },
                            {
                                "name": "Low Quality: Failed Keypass",
                                "color": "#a5a5a5",
                                "value": base_caller_stats["failed_keypass"],
                            },
                            {
                                "name": "Low Quality: Quality Trim",
                                "color": "#a5a5a5",
                                "value": base_caller_stats["quality_trim"],
                            },
                        ],
                    },
                ],
            },
            {"name": "Excluded", "value": sigproc_stats["excluded wells"]},
            {"name": "Ignored", "value": sigproc_stats["ignored wells"]},
            {"name": "Empties", "value": sigproc_stats["empty wells"]},
            {"name": "Pinned", "value": sigproc_stats["pinned wells"]},
        ],
    }
    write_results_from_template(
        {"data": data}, output_path, os.path.dirname(os.path.realpath(__file__))
    )

    total_wells = check_total_wells(data)
    if total_wells != sigproc_stats["total wells"]:
        return print_warning(
            "Well totals inconsistent! {:,.0f} vs {:,.0f} This requires a fix on the TS software.".format(
                total_wells, sigproc_stats["total wells"]
            )
        )

    return print_info("See results for details.")


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
