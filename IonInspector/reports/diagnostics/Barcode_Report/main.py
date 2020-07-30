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
    def get_barcode_name(read_key, read_group):
        # "barcode_name" is not present, it can be combined barcode or no barcode
        if "barcode_name" not in read_group:
            if "." in read_key:
                # combined barcodes
                return read_key.split(".").pop()
            else:
                # a non-barcode rerun
                return "No Barcode"

        return read_group.get("barcode_name")

    groups = []
    for key, value in datasets_basecaller_object["read_groups"].iteritems():
        groups.append(
            {
                "filtered": value.get("filtered", False) or "nomatch" in key,
                "sample_name": value.get("sample", "N/A"),
                "name": get_barcode_name(read_key=key, read_group=value),
                "end_barcode": value.get("end_barcode", {}).get("barcode_name", ""),
                "read_count": value.get("read_count", 0),
                "index": value.get("index", -1),
                "group": key,
                "nuc_type": value.get("nucleotide_type", "")
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
    # group, sparkline_path, histogram_data, inline_control
    if archive_type == "Valkyrie":
        histograms_first_pass = []
        sample_mapping = {}
        for group in groups:
            barcode_name = group["name"]
            src_image_path = os.path.join(
                archive_path, "CSA/outputs/BaseCallingActor-00/{}_rawlib.inline_control.png".format(barcode_name)
            )
            dst_image_path = os.path.join(
                output_path, "{}.inline_control.png".format(barcode_name)
            )

            if os.path.exists(src_image_path):
                # Copy to test dir
                shutil.copyfile(src_image_path, dst_image_path)
                inline_path = os.path.basename(dst_image_path)
            else:
                inline_path = None

            sample_name = group["sample_name"]
            if sample_name != "N/A":  # single barcode
                sample_mapping[barcode_name] = sample_name

            histograms_first_pass.append(
                {
                    "group": group,
                    "histogram_data": json.dumps(get_histogram_data(archive_path, group["name"])),
                    "inline_path": inline_path
                }
            )

        # fill missing sample name based on barcode name match
        # will go by the last matched barcode
        for hist in histograms_first_pass:
            if hist["group"]["sample_name"] == "N/A":
                for barcode_name, sample_name in sample_mapping.items():
                    if barcode_name in hist["group"]["name"]:
                        hist["group"]["sample_name"] = sample_name

        # first sort by sample name, then by index
        # combined barcode has index of -1, so it would go first
        histograms_sorted = sorted(histograms_first_pass,
                                   key=lambda hist: (hist["group"]["sample_name"], hist["group"]["index"]))

        # transform to list of list
        for hist in histograms_sorted:
            histograms.append([
                hist["group"],
                None,
                hist["histogram_data"],
                hist["inline_path"]
            ])

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
                histograms.append([group, os.path.basename(dst_image_path), None, None])
            else:
                histograms.append([group, None, None, None])

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
