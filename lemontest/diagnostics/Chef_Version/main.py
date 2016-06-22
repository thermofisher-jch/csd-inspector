#!/usr/bin/env python

import fnmatch
import json
import os
import sys
from django.template import Context, Template
from lemontest.diagnostics.common.inspector_utils import *

def find_summary(matches):
    """
    Helper method for finding the chef package version
    :param matches: a list of file paths to the gui logs
    :return: The string summary of the check package version
    """

    for match in matches:
        for line in open(match):
            if 'chefPackageVer' in line:
                # we expect this to be a json output and will split on it primary delimiter
                json_text = '{' + line.split('{', 1)[1]
                info = json.loads(json_text)
                return info['chefPackageVer']
    return "Could not find any gui log to look up the chef version."


try:
    archive, output = sys.argv[1:3]
    context = {
        "serial": "None",
        "versions": [],
    }

    matches = list()
    for root, dirnames, filenames in os.walk(os.path.join(archive, 'var', 'log', 'IonChef', 'ICS')):
        for filename in fnmatch.filter(filenames, 'gui-*.log'):
            matches.append(os.path.join(root, filename))

    root = get_xml_from_run_log(archive)
    name_tag = root.find("Versions/is")
    is_name = name_tag.text
    name_tag = root.find("Versions/scripts")
    scripts_name = name_tag.text
    context['versions'] = [(t.tag, t.text) for t in root.findall("Versions/*")]
    context['serial'] = root.find("Instrument/serial").text

    summary = find_summary(matches)

    print_info(summary)
    template = Template(open("results.html").read())
    result = template.render(Context(context))
    with open(os.path.join(output, "results.html"), 'w') as out:
        out.write(result.encode("UTF-8"))

except Exception as exc:
    print_na(str(exc))
