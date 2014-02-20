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
    headers = []
    warnings = []
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
        try:
            tree = ElementTree.parse(xml_path)
        except Exception as err:
            errors.append("Error reading run log: " + str(err))
        else:
            root = tree.getroot()
            notes = root.findall("System_Run/sys_info")
            if notes:
                headers = [t.tag for t in notes[0].getchildren()]
            for note in notes:
                notifications.append(tuple([t.text for t in note.getchildren()]))
            warns = root.findall("Warnings_Run/warning")
            if warns:
                headers = [t.tag for t in warns[0].getchildren()]
            for warn in warns:
                warnings.append(tuple([t.text for t in warn.getchildren()]))
            notifications = sorted(list(set(notifications) - set(warnings)))

    context = {
        "files": files,
        "warnings": notifications,
        "headers": headers,
        "xml_path": rel_xml_path,
        "errors": errors
    }
    template = Template(filename="logs.mako")
    result = template.render(**context)
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
        summary += "{} notifications.".format(len(warnings))
    else:
        print("OK")
        print("10")
    print(summary)