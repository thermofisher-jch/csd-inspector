#!/usr/bin/env python

import json
import os
import shutil
import sys

import numpy

from IonInspector.reports.diagnostics.common.inspector_utils import (
    write_results_from_template,
    print_info,
    handle_exception,
)


def get_read_group_file_prefixes(datasets_basecaller_object):
    file_prefixes = {}
    for item in datasets_basecaller_object["datasets"]:
        for group in item["read_groups"]:
            file_prefixes[group] = item["file_prefix"]
    return file_prefixes


def get_read_groups(datasets_basecaller_object):
    groups = []
    for key, value in datasets_basecaller_object["read_groups"].iteritems():
        groups.append(
            {
                "filtered": value.get("filtered", False) or "nomatch" in key,
                "name": value.get("barcode_name", "No Barcode"),
                "end_barcode": value.get("end_barcode", {}).get("barcode_name", ""),
                "read_count": value.get("read_count", 0),
                "index": value.get("index", -1),
                "group": key,
            }
        )
    return sorted(groups, key=lambda k: k["index"])


def get_histogram_data(archive_path, barcode):
    if barcode == "No Barcode":
        barcode = "nomatch"
    ionstats_basecaller_path = os.path.join(
        archive_path,
        "CSA/outputs/BaseCallingActor-00/{}_rawlib.ionstats_basecaller.json".format(
            barcode
        ),
    )
    if os.path.exists(ionstats_basecaller_path):
        with open(ionstats_basecaller_path) as fp:
            ionstats_basecaller = json.load(fp)
            return list(enumerate(ionstats_basecaller["full"]["read_length_histogram"]))
    else:
        return []


def execute(archive_path, output_path, archive_type):
    if archive_type == "Valkyrie":
        datasets_path = "CSA/outputs/BaseCallingActor-00/datasets_basecaller.json"
    else:
        datasets_path = "basecaller_results/datasets_basecaller.json"

    with open(os.path.join(archive_path, datasets_path)) as datasets_file:
        datasets_object = json.load(datasets_file)

    prefixes = get_read_group_file_prefixes(datasets_object)
    groups = get_read_groups(datasets_object)

    # get all of the filtered data sets
    total_reads = sum([float(x["read_count"]) for x in groups])
    filtered_data = [float(x["read_count"]) for x in groups if not x["filtered"]]
    mean = numpy.mean(filtered_data)
    min_read_cound = numpy.min(filtered_data) if filtered_data else 0
    std = numpy.std(filtered_data)

    histograms = []
    if archive_type == "Valkyrie":
        for group in groups:
            histograms.append(
                [
                    group,
                    None,
                    json.dumps(get_histogram_data(archive_path, group["name"])),
                ]
            )
    else:
        for group in groups:
            prefix = prefixes[group["group"]]
            src_image_path = os.path.join(
                archive_path, "basecaller_results/{}.sparkline.png".format(prefix)
            )
            dst_image_path = os.path.join(
                output_path, "{}.sparkline.png".format(prefix)
            )
            if os.path.exists(src_image_path):
                # Copy to test dir
                shutil.copyfile(src_image_path, dst_image_path)
                histograms.append([group, os.path.basename(dst_image_path), None])
            else:
                histograms.append([group, None, None])

    write_results_from_template(
        {
            "histograms": histograms,
            "total_reads": total_reads,
            "mean": mean,
            "std": std,
            "cv": (std / mean) * 100.0 if mean != 0.0 else 0,
            "min_percent": (min_read_cound / mean) * 100.0 if mean != 0.0 else 0,
        },
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )
    return print_info("See results for details.")


if __name__ == "__main__":
    execute(archive_path=sys.argv[1], output_path=sys.argv[2], archive_type=sys.argv[3])
