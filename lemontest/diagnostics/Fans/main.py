#!/usr/bin/env python

import sys
import os
import os.path
from django.template import Context, Template
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fan_names = [
    "Below Deck Chassis Fan",
    "Solutions Cartridge (Front Zone) Fan",
    "Reagents Cartridge (Back Zone) Fan",
    "Above Deck Fan 1",
    "Above Deck Fan 2",
    "Recovery Centrifuge Motor Fan"
]

def plot_fan_speed(time, speed, name):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(time, speed)
    ax.set_title("Ion Chef {} Speed".format(name))
    ax.set_xlabel("Time")
    ax.set_ylabel("Fan Speed in Revolutions/second")
    path = "{}.png".format(name)
    figure_path = os.path.join(output, path)
    fig.savefig(figure_path, dpi=90)
    return path

if __name__ == "__main__":
    archive, output = sys.argv[1:3]
    file_count = 0
    files = []
    headers = []
    warnings = []
    csv_path = ''
    rel_csv_path = ''
    errors = []
    error_summary = ""
    
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
            cols = [(float(r[0]), int(r[6]), int(r[8]), int(r[9]), int(r[10]), int(r[11]), int(r[12])) for r in reader]
        if len(cols) == 0:
            error_summary = "No flow rate information"
        else:
            columns = zip(*cols)
            time = columns[0]
            fans = columns[1:]
            for name, speed in zip(fan_names, fans):
                plot_fan_speed(time, speed, name)

            context = Context({
                "plots": map(lambda s: s + ".png", fan_names)
            })
            template = Template(open("results.html").read())
            result = template.render(context)
            with open(os.path.join(output, "results.html"), 'w') as out:
                out.write(result.encode("UTF-8"))
    else:
        error_summary = "No run log CSV"

    if error_summary:
        print("N/A")
        print(0)
        print(error_summary)
    else:
        print("Info")
        print("20")
