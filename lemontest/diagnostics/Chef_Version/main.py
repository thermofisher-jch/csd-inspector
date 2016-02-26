#!/usr/bin/env python

from xml.etree import ElementTree
import xml.etree 
import sys
import os
import os.path
import re
from mako.template import Template


if __name__ == "__main__":
    archive, output = sys.argv[1:3]
    file_count = 0
    files = []
    output_name = ''
    xml_path = ''
    errors = []
    context = {
        "serial": "None",
        "versions": [],
    }
    
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
            name_tag = root.find("Versions/is")
            is_name = name_tag.text
            name_tag = root.find("Versions/scripts")
            scripts_name = name_tag.text
            output_name = "is: {} scripts: {}".format(is_name, scripts_name)
            context['versions'] = [(t.tag, t.text) for t in root.findall("Versions/*")]
            context['serial'] = root.find("Instrument/serial").text

        summary = output_name
        print("Info")
        print("20")
        print(summary)
        
        template = Template(filename="results.mako")
        result = template.render(**context)
        with open(os.path.join(output, "results.html"), 'w') as out:
            out.write(result.encode("UTF-8"))

    else:
        summary = "No Run Log."
        print("N/A")
        print("0")
        print(summary)

