#!/usr/bin/env python

import fnmatch
import json
import os
import sys
from mako.template import Template
from lemontest.diagnostics.common.inspector_utils import *


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

    summary = "Could not find any gui log to look up the chef version."
    if len(matches) > 0:
        for line in open(matches[0]):
            if 'chefPackageVer' in line:
                # we expect this to be a json output and will split on it primary delimiter
                json_text = '{' +  line.split('{', 1)[1]
                info = json.loads(json_text)
                summary = info['chefPackageVer']

    print_info(summary)
    template = Template(filename="results.mako")
    result = template.render(**context)
    with open(os.path.join(output, "results.html"), 'w') as out:
        out.write(result.encode("UTF-8"))

except Exception as exc:
    print_na(str(exc))
