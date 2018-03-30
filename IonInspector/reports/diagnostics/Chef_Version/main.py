#!/usr/bin/env python

import fnmatch
import json
import os
import sys
from django.template import Context, Template
from IonInspector.reports.diagnostics.common.inspector_utils import *


def find_summary(gui_log_paths):
    """
    Helper method for finding the chef package version
    :param matches: a list of file paths to the gui logs
    :return: The string summary of the check package version
    """
    for gui_log_path in gui_log_paths:
        with open(gui_log_path) as guil_log_handle:
            for line in guil_log_handle.readlines():
                if 'chefPackageVer' in line:
                    # we expect this to be a json output and will split on it primary delimiter
                    json_text = '{' + line.split('{', 1)[1]
                    info = json.loads(json_text)
                    return info['chefPackageVer']
    return "Could not find any gui log to look up the chef version."


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        context = {
            "serial": "None",
            "versions": [],
        }

        gui_log_path_matches = list()
        for root, dirnames, filenames in os.walk(os.path.join(archive_path, 'var', 'log', 'IonChef', 'ICS')):
            for filename in fnmatch.filter(filenames, 'gui-*.log'):
                gui_log_path_matches.append(os.path.join(root, filename))

        root = get_xml_from_run_log(archive_path)
        name_tag = root.find("Versions/is")
        is_name = name_tag.text
        name_tag = root.find("Versions/scripts")
        scripts_name = name_tag.text
        context['versions'] = [(t.tag, t.text) for t in root.findall("Versions/*")]
        context['serial'] = root.find("Instrument/serial").text
        release_version_node = root.find("Versions/release")
        summary = release_version_node.text if release_version_node is not None else find_summary(gui_log_path_matches)
        write_results_from_template(context, output_path, os.path.dirname(os.path.realpath(__file__)))
        return print_info(summary)
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    execute(sys.argv[1], sys.argv[2], sys.argv[3])
