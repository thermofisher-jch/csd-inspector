#!/usr/bin/env python

import sys
import os
import ConfigParser

def load_ini(file_path, namespace="global"):
    parse = ConfigParser.ConfigParser()
    parse.optionxform = str # preserve the case
    parse.read(file_path)
    return dict(parse.items(namespace))


def check_chip(archive_path):
    path = os.path.join(archive_path, "explog_final.txt")
    if not os.path.exists(path):
        path = os.path.join(archive_path, "explog.txt")
    if os.path.exists(path):
        for line in open(path):
            if line.startswith("ChipType:"):
                return line.split(":", 1)[-1].strip()


archive_path, output_path = sys.argv[1:3]

if check_chip(archive_path) == "314R":
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
