#!/usr/bin/env python

from xml.etree import ElementTree
import xml.etree 
import sys
import os
import os.path
from mako.template import Template

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
            tree = ElementTree.parse(xml_path)
        except Exception as err:
            errors.append("Error reading run log: " + str(err))
        else:
            root = tree.getroot()
            name_tag = root.find("RunInfo/kit")
            if name_tag is None:
                error_summary = "No kit info"
            else:
                output_name = name_tag.text
    else:
        error_summary = "No Run Log."

    if error_summary:
        print("N/A")
        print("0")
        print(error_summary)
    else:
        summary = output_name
        print("Info")
        print("20")
        print(summary)


