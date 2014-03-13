#!/usr/bin/env python

import sys
import os
import os.path
from mako.template import Template
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

if __name__ == "__main__":
    archive, output = sys.argv[1:3]
    file_count = 0
    files = []
    headers = []
    warnings = []
    csv_path = ''
    rel_csv_path = ''
    errors = []
    
    for path, dirs, names in os.walk(archive):
        if "test_results" not in path:
            for name in names:
                if "logs.tar" not in name:
                    rel_dir = os.path.relpath(path, archive)
                    rel = os.path.join(rel_dir, name)
                    full = os.path.join(path, name)
                    files.append(rel)
                    file_count += 1
                    if rel.startswith("var/log/IonChef/RunLog/") and rel.endswith(".csv"):
                        csv_path = full
                        res_csv_path = rel

    if csv_path:
        with open(csv_path) as csvfile:
            reader = csv.reader(csvfile)
            header = reader.next()
            cols = [(float(r[0]), int(r[7])) for r in reader]
            time, flows = zip(*cols)
        plt.plot(time, flows)
        plt.title("Ion Chef Liquid Cooling: Flowmeter")
        plt.xlabel("Time")
        plt.ylabel("Flow Rate in Hz")
        figure_path = os.path.join(output, "plot.png")
        plt.savefig(figure_path, dpi=90)

    context = {}
    template = Template(filename="logs.mako")
    result = template.render(**context)
    with open(os.path.join(output, "results.html"), 'w') as out:
        out.write(result.encode("UTF-8"))
    summary = ""
    print("Info")
    print("20")
