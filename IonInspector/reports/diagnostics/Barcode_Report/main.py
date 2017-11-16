#!/usr/bin/env python

import os
import shutil
import sys
import json

from IonInspector.reports.diagnostics.common.inspector_utils import write_results_from_template, print_info


def get_read_group_file_prefixes(datasets_basecaller_object):
    file_prefixes = {}
    for item in datasets_basecaller_object["datasets"]:
        for group in item["read_groups"]:
            file_prefixes[group] = item["file_prefix"]
    return file_prefixes


def get_read_groups(datasets_basecaller_object):
    groups = []
    for key, value in datasets_basecaller_object["read_groups"].iteritems():
        groups.append({
            "filtered": value.get("filtered", False),
            "name": value.get("barcode_name", "nomatch"),
            "read_count": value.get("read_count", 0),
            "index": value.get("index", -1),
            "group": key
        })
    return sorted(groups, key=lambda k: k['index'])


def get_read_length_histograms(archive_path, output_path):
    with open(os.path.join(archive_path, "basecaller_results/datasets_basecaller.json")) as datasets_file:
        datasets_object = json.load(datasets_file)

    prefixes = get_read_group_file_prefixes(datasets_object)
    groups = get_read_groups(datasets_object)

    histograms = []
    for group in groups:
        prefix = prefixes[group["group"]]
        src_image_path = os.path.join(archive_path, "basecaller_results/{}.sparkline.png".format(prefix))
        dst_image_path = os.path.join(output_path, "{}.sparkline.png".format(prefix))
        if os.path.exists(src_image_path):
            # Copy to test dir
            shutil.copyfile(src_image_path, dst_image_path)
            histograms.append([group, os.path.basename(dst_image_path)])
        else:
            histograms.append([group, None])
    return histograms


def execute(archive_path, output_path, archive_type):
    try:
        write_results_from_template({
            'histograms': get_read_length_histograms(archive_path, output_path)
        }, output_path)
        return print_info("See results for details.")
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
