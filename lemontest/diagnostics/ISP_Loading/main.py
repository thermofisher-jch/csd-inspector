#!/usr/bin/env python

import sys
import os
import ConfigParser
from lemontest.diagnostics.common.inspector_utils import *


def load_ini(file_path, namespace="global"):
    parse = ConfigParser.ConfigParser()
    parse.optionxform = str # preserve the case
    parse.read(file_path)
    return dict(parse.items(namespace))

archive_path, output_path = sys.argv[1:3]
explog = read_explog(archive_path)
if explog['ChipType'] == "314R":
    print("N\A")
    print(0)
    print("Loading for 314 chips is not actionable :(")
    sys.exit()

stats_path = None
files = ['sigproc_results/analysis.bfmask.stats', 'sigproc_results/bfmask.stats']
for file_name in files:
    path = os.path.join(archive_path, file_name)
    if os.path.exists(path):
        stats_path = path
        break

if stats_path:
    data = load_ini(stats_path)
    bead_loading = float(data["Bead Wells"]) / (float(data["Total Wells"]) - float(data["Excluded Wells"]))
    if bead_loading >= 0.7:
        print("OK")
        print(10)
    elif bead_loading >= 0.4:
        print("Warning")
        print(30)
    else:
        print("Alert")
        print(40)
    print("{:.1%} of wells found ISPs".format(bead_loading))
else:
    print("N/A")
    print(0)
    print("Required stats files not included")
