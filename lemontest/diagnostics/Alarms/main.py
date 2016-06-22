#!/usr/bin/env python

import sys
import os
import os.path
import re
import xml.etree 
from datetime import datetime
from xml.etree import ElementTree
from django.template import Context, Template

if __name__ == "__main__":
    archive, output = sys.argv[1:3]
    file_count = 0
    files = []
    headers = []
    warnings = []
    xml_path = ''
    rel_xml_path = ''
    errors = []

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
                        rel_xml_path = rel


    if xml_path:
        # groom the xml of known error conditions
        xml = ''
        with open(xml_path, 'r') as xml_file:
            xml = xml_file.read()

        xml = re.sub('< *', '<', xml)
        xml = re.sub('</ *', '</', xml)
        xml = re.sub('> *', '>', xml)

        try:
            root = ElementTree.fromstring(xml)
        except Exception as err:
            errors.append("Error reading run log: " + str(err))
        else:
            warns = root.findall("Warnings_Run/warning")
            if warns:
                headers = [t.tag for t in warns[0].getchildren()]
            for warn in warns:
                record = [t.text for t in warn.getchildren()]
                if len(record) > 0:
                    d = datetime.strptime(record[0], "%Y%m%d_%H%M%S")
                    record[0] = d.strftime("%Y %b %d %H:%M:%S")
                    warnings.append(record)

    context = Context({
        "files": files,
        "warnings": warnings,
        "headers": headers,
        "xml_path": rel_xml_path,
        "errors": errors
    })
    template = Template(open("logs.html").read())
    result = template.render(context)
    with open(os.path.join(output, "results.html"), 'w') as out:
        out.write(result.encode("UTF-8"))
    summary = ""
    if not rel_xml_path:
        summary += "No Run Log."
    if errors:
        print("Alert")
        print("40")
    elif warnings:
        print("Warning")
        print("30")
        summary += "{} alarms.".format(len(warnings))
    else:
        print("OK")
        print("10")
    print(summary)