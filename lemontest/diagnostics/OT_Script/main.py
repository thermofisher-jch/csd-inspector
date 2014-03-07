#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import sys
import os.path
from mako.template import Template


scripts = {
    "PGM_20_10_10_98C_30s_denature.txt": "Ion PGM™ Template OT2 200 Kit",
    "custom_4_98-91C.txt": "Ion PGM™ Template OT2 400 Kit",
    "OT2_Proton.txt": "Ion Proton™ I Template OT2 Kit",
    "OT2_Proton_200-v2.txt": "Ion PI™ Template OT2 200 Kit v2",
    "custom_1_OT2_Proton_200-v2_XT.txt": "Ion PI™ Template OT2 200 Kit v2 with XT",
    "script_Proton_OT2_200_Kit_v3.txt": "Ion PI™ Template OT2 200 Kit v3",
    "OT2_Proton.txt": "Ion PI™ Template OT2 200 Kit",
    "charged_cleaning.txt": "Clean Instrument",
    "initialize.txt": "Initialize",
    "centrifuge_proton.txt": "Centrifuge",
    "tuv_testing.txt": "TUV Test",
    "initialize_factory.txt": "System test: Prime",
    "system_test.txt": "System test: Factory Test",
    "purge.txt": "System test: Purge"
}

archive, output = sys.argv[1:3]
path = os.path.join(archive, "onetouch.log")
with open(path) as log:
    script_line = log.readline()

columns = script_line.split(',')
script = os.path.basename(columns[0])
if script in scripts:
    script = scripts[script]

rows = []
for col in columns:
    if ":" in col:
        row = [r.strip() for r in col.split(":", 1)]
        rows.append(row)

context = {
    "script_line": script_line,
    "rows": rows
}
template = Template(filename="results.mako")
result = template.render(**context)
with open(os.path.join(output, "results.html"), 'w') as out:
    out.write(result.encode("UTF-8"))

print("Info")
print("20")
print(script)
