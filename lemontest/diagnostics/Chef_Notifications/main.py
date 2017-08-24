#!/usr/bin/env python

import sys
import os.path
from datetime import datetime
from django.template import Context, Template

from lemontest.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    file_count = 0
    files = []
    headers = []
    warnings = set()
    notifications = []
    xml_path = ''
    rel_xml_path = ''
    errors = []

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
                        rel_xml_path = rel

    if xml_path:
        try:
            root = get_xml_from_run_log(archive_path)
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
    with open(os.path.join(output_path, "results.html"), 'w') as out:
        out.write(result.encode("UTF-8"))
    summary = ""
    if not rel_xml_path:
        summary += "No Run Log."
    if errors:
        print("Alert")
        print("40")
    elif notifications:
        print("Alert")
        print("30")
        summary += "{} notifications.".format(len(notifications))
    else:
        print("OK")
        print("10")
    print(summary)

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
