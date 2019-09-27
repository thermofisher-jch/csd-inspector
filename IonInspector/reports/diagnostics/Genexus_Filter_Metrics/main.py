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
    return stats["Filtering"]["ReadDetails"]["lib"], stats["Filtering"]["BaseDetails"]


def check_total_wells(data):
    if "value" in data:
        return data["value"]
    elif "children" in data:
        return sum([check_total_wells(c) for c in data["children"]])
    else:
        raise ValueError("Child must have value or children!")


def execute(archive_path, output_path, archive_type):
    sigproc_stats = parse_sigproc_stats(archive_path)
    base_caller_read_stats, base_caller_base_stats = parse_base_caller_stats(archive_path)
    summary = {
        "loading_per": 100 * (sigproc_stats["bead wells"] / (sigproc_stats["total wells"] - sigproc_stats["excluded wells"])),
        "loading": sigproc_stats["bead wells"],

        "enrichment_per": 100 * (sigproc_stats["live beads"] / sigproc_stats["bead wells"]),
        "enrichment": sigproc_stats["live beads"],

        "library_per": 100 * (sigproc_stats["library beads"] / sigproc_stats["live beads"]),
        "library": sigproc_stats["library beads"],

        "final_reads_per": 100 * (base_caller_read_stats["valid"] / sigproc_stats["library beads"]),
        "final_reads": base_caller_read_stats["valid"],

        "total_bases": base_caller_base_stats["final"],
    }
    data = {
        "name": "Active Lane Wells",
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
                                "value": base_caller_read_stats["valid"],
                            },
                            {
                                "name": "Polyclonal",
                                "value": base_caller_read_stats["bkgmodel_polyclonal"],
                            },
                            {
                                "name": "Primer Dimer",
                                "value": base_caller_read_stats["adapter_trim"],
                            },
                            {
                                "name": "Quality Filter",
                                "value": base_caller_read_stats["quality_filter"],
                            },
                            {
                                "name": "Low Quality: High PPF",
                                "color": "#a5a5a5",
                                "value": base_caller_read_stats["bkgmodel_high_ppf"],
                            },
                            {
                                "name": "Low Quality: Bad Key",
                                "color": "#a5a5a5",
                                "value": base_caller_read_stats["bkgmodel_keypass"],
                            },
                            {
                                "name": "Low Quality: Short Read",
                                "color": "#a5a5a5",
                                "value": base_caller_read_stats["short"],
                            },
                            {
                                "name": "Low Quality: Failed Keypass",
                                "color": "#a5a5a5",
                                "value": base_caller_read_stats["failed_keypass"],
                            },
                            {
                                "name": "Low Quality: Quality Trim",
                                "color": "#a5a5a5",
                                "value": base_caller_read_stats["quality_trim"],
                            },
                            {
                                "name": "Low Quality: Barcode Trim",
                                "color": "#a5a5a5",
                                "value": base_caller_read_stats["barcode_trim"],
                            },
                            {
                                "name": "Low Quality: Tag Trim",
                                "color": "#a5a5a5",
                                "value": base_caller_read_stats["tag_trim"],
                            },
                        ],
                    },
                ],
            },
            {"name": "Ignored", "value": sigproc_stats["ignored wells"]},
            {"name": "Empties", "value": sigproc_stats["empty wells"]},
            {"name": "Pinned", "value": sigproc_stats["pinned wells"]},
        ],
    }

    total_wells = check_total_wells(data)
    active_wells = sigproc_stats["total wells"] - sigproc_stats["excluded wells"]

    warning = None
    if total_wells != active_wells:
        warning = "Well totals inconsistent! {:,.0f} vs {:,.0f} This requires a fix on the TS software." \
                  "The totals below do not include any wells categorized as 'Barcode Trim'!".format(
            total_wells, active_wells
        )

    write_results_from_template(
        {"data": data, "warning": warning, "summary": summary},
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    return print_info("See results for details.")


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
