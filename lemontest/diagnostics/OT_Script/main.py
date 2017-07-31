#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import sys
import os.path
from django.template import Context, Template


scripts = {
    "PGM_20_10_10_98C_30s_denature.txt": u"Ion PGM™ Template OT2 200 Kit",
    "custom_4_98-91C.txt": u"Ion PGM™ Template OT2 400 Kit",
    "OT2_Proton.txt": u"Ion Proton™ I Template OT2 Kit",
    "OT2_Proton_200-v2.txt": u"Ion PI™ Template OT2 200 Kit v2",
    "custom_1_OT2_Proton_200-v2_XT.txt": u"Ion PI™ Template OT2 200 Kit v2 with XT",
    "script_Proton_OT2_200_Kit_v3.txt": u"Ion PI™ Template OT2 200 Kit v3",
    "OT2_Proton.txt": u"Ion PI™ Template OT2 200 Kit",
    "charged_cleaning.txt": u"Clean Instrument",
    "initialize.txt": u"Initialize",
    "centrifuge_proton.txt": u"Centrifuge",
    "tuv_testing.txt": u"TUV Test",
    "initialize_factory.txt": u"System test: Prime",
    "system_test.txt": u"System test: Factory Test",
    "purge.txt": u"System test: Purge"
}

kit_times = {
    u"Ion PGM™ Template OT2 200 Kit"            : "5 hr 30 min",
    u"Ion PGM™ Template OT2 400 Kit"            : "8 hr",
    u"Ion Proton™ I Template OT2 Kit"           : "6 hr 15 min",
    u"Ion PI™ Template OT2 200 Kit v2"          : "6 hr 30 min",
    u"Ion PI™ Template OT2 200 Kit v2 with XT"  : "9 hr",
    u"Ion PI™ Template OT2 200 Kit v3"          : "6 hr 30 min"
}


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    path = os.path.join(archive_path, "onetouch.log")
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

    summary = script

    time = kit_times.get(script, None)
    if time:
        summary += ": Expected run time %s" % time

    context = Context({
        "script_line": script_line,
        "rows": rows,
        "time": time,
    })
    template = Template(open("results.html").read())
    result = template.render(context)
    with open(os.path.join(output_path, "results.html"), 'w') as out:
        out.write(result.encode("UTF-8"))

    print("Info")
    print("20")
    print(summary.encode("UTF-8"))

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
