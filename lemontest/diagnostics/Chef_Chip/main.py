#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    file_count = 0
    files = []
    output_name = ''
    xml_path = ''
    error_summary = ""

    for path, dirs, names in os.walk(archive_path):
        if "test_results" not in path:
            for name in names:
                if "logs.tar" not in name:
                    rel_dir = os.path.relpath(path, archive_path)
                    rel = os.path.join(rel_dir, name)
                    full = os.path.join(path, name)
                    files.append(rel)
                    file_count += 1
                    if rel.startswith("var/log/IonChef/RunLog/") and rel.endswith(".xml"):
                        xml_path = full

    if xml_path:
        try:
            root = get_xml_from_run_log(archive_path)
        except Exception as err:
            handle_exception(err, output_path)
            return
        else:
            name_tag = root.find("RunInfo/chip")
            if name_tag is None:
                error_summary = "No chip info"
            else:
                output_name = name_tag.text.strip()
                if output_name.isdigit():
                    chip_number = int(output_name)
                    if chip_number < 10:
                        name_tag = root.find("RunInfo/chipVersion")
                        version = name_tag.text.strip()
                        output_name = "P{}v{}".format(chip_number, version)
    else:
        error_summary = "No Run Log."

    if error_summary:
        print_na(error_summary)
    else:        
        print_info(output_name)

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
