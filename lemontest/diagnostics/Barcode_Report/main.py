#!/usr/bin/env python

import glob
import os
import shutil
import sys

from lemontest.diagnostics.common.inspector_utils import write_results_from_template, print_info


def get_read_length_histograms(archive_path, output_path):
    histograms = []
    for image_path in glob.glob(os.path.join(archive_path, "basecaller_results/*sparkline.png")):
        image_filename = os.path.basename(image_path)
        # Copy to test dir
        shutil.copyfile(image_path, os.path.join(output_path, image_filename))
        # Generate name and path
        name = image_filename.replace(".sparkline.png", "")
        histograms.append((name, image_filename))
    return histograms


def execute(archive_path, output_path, archive_type):
    write_results_from_template({
        'histograms': get_read_length_histograms(archive_path, output_path)
    }, output_path)
    print_info("See results for details.")


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
