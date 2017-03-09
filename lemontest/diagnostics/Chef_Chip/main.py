#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *

if __name__ == "__main__":
    archive, output = sys.argv[1:3]
    file_count = 0
    files = []
    output_name = ''
    xml_path = ''
    errors = []
    error_summary = ""

    for path, dirs, names in os.walk(archive):
        if "test_results" not in path:
            for name in names:
                if "logs.tar" not in name:
                    rel_dir = os.path.relpath(path, archive)
                    rel = os.path.join(rel_dir, name)
                    full = os.path.join(path, name)
                    files.append(rel)
                    file_count += 1
                    if rel.startswith("var/log/IonChef/RunLog/") and rel.endswith(".xml"):
                        xml_path = full

    if xml_path:
        try:
            root = get_xml_from_run_log(archive)
        except Exception as err:
            handle_exception(err, output)
            exit()
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


