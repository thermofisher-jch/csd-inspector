#!/usr/bin/env python

import sys
import os.path
from datetime import datetime
from IonInspector.reports.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        files = []
        headers = []
        warnings = []
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
                    headers = [t.tag for t in warns[0].getchildren()]
                for warn in warns:
                    record = [t.text for t in warn.getchildren()]
                    if len(record) > 0:
                        d = datetime.strptime(record[0], "%Y%m%d_%H%M%S")
                        record[0] = d.strftime("%Y %b %d %H:%M:%S")
                        warnings.append(record)

        write_results_from_template({
            "files": files,
            "warnings": warnings,
            "headers": headers,
            "xml_path": rel_xml_path,
            "errors": errors
        }, output_path)

        summary = ""
        if not rel_xml_path:
            summary += "No Run Log."
        if errors:
            return print_alert(summary)
        elif warnings:
            summary += "{} alarms.".format(len(warnings))
            return print_warning(summary)
        else:
            return print_ok(summary)
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    execute(sys.argv[1], sys.argv[2], sys.argv[3])

