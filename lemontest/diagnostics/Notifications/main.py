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
    warnings = set()
    notifications = []
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
                warn_headers = [t.tag for t in warns[0].getchildren()]
            for warn in warns:
                record = [t.text for t in warn.getchildren()]
                if len(record) >= 3:
                    warnings.add((record[0], record[2]))
            notes = root.findall("System_Run/sys_info")
            if notes:
                headers = [t.tag for t in notes[0].getchildren()]
            for note in notes:
                record = [t.text for t in note.getchildren()]
                if len(record) >= 3 and tuple(record[:2]) not in warnings:
                    d = datetime.strptime(record[0], "%Y%m%d_%H%M%S")
                    record[0] = d.strftime("%Y %b %d %H:%M:%S")
                    notifications.append(record)

    context = Context({
        "files": files,
        "warnings": notifications,
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
    elif notifications:
        print("Warning")
        print("30")
        summary += "{} notifications.".format(len(notifications))
    else:
        print("OK")
        print("10")
    print(summary)