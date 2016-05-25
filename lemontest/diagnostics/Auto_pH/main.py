#!/usr/bin/env python

import os
import re
import sys
from lemontest.diagnostics.common.inspector_utils import *

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def is_proton(init_log):
    """
    Determines if the archive is a proton
    :param init_log: The lines of the InitLog.txt
    :return: a boolean true if this is a proton
    """

    for log_line in init_log:
        if log_line.startswith('Proton Release_version'):
            return True

    return False

try:
    # data to be populated
    failure = ""
    starting_ph = -1.0
    reagent_check = "unknown"
    raw_traces = list()
    x = list()
    y = list()

    # get the paths
    archive_path, output_path = sys.argv[1:3]
    init_log_path = os.path.join(archive_path, 'InitLog.txt')
    if not os.path.exists(init_log_path):
        raise Exception("InitLog.txt is not present so test cannot be run.")

    # read in the init log lines
    init_log = list()
    with open(init_log_path, 'r') as init_log_handle:
        init_log = init_log_handle.readlines()

    # TODO: perhaps move this to a template
    with open(os.path.join(output_path, "results.html"), 'w') as html_handle:
        html_handle.write("<html><link rel=stylesheet href=some.css type=text/css>\n")
        html_handle.write("</head><body>")
        html_handle.write("<h1 align=\"center\">AutopH plot</h1>")

        if is_proton(init_log):
            for line in init_log:
                if line.startswith("AUTOPH"):
                    bits = line.split(" ")
                    previous_x = x[-1] if len(x) > 0 else 0.0
                    x.append(float(bits[-1]) + previous_x)
                    y.append(bits[6])

                elif line.startswith("ErrorMsgBeginOvershot Target pH"):
                    # TODO: report the amount it overshot by
                    failure = "Overshot the pH."

                elif line.startswith("ErrorMsgBeginUndershot Target pH"):
                    # TODO: report the amount it undershot by
                    failure = "Undershot the pH."
                elif line.startswith("Initial W2 pH="):
                    starting_ph = float(line.split('=')[1])
                elif line.startswith("Rawtrace:"):
                    reagent_check = line.split(": ")[1]
                elif re.search("[WR]\dpH", line):
                    raw_traces.append(line.strip())

        else:
            # logic for getting PGM data
            for line in init_log:
                if re.search("^\d+\)", line):
                    # get the ph, but let the next one be the end value for the current step
                    if "W2 pH=" in line:
                        step_ph = float(line.split('=')[1])
                        if starting_ph == -1:
                            starting_ph = step_ph
                        else:
                            y.append(step_ph)

                    elif "Adding" in line:
                        volume_added = float(line.split(' ')[2])
                        if len(x) == 0:
                            x.append(volume_added)
                        else:
                            x.append(volume_added + x[-1])
                elif line.startswith("FAILEDUNDERSHOT"):
                    failure = "Undershot the pH."
                elif line.startswith("RawTraces:"):
                    reagent_check = line.split(": ")[1]
                elif line.startswith("RawTraces "):
                    raw_traces.append(line.split(" ", 1)[1])

        # check to make sure we get all of the required information
        if len(x) == 0 or len(y) == 0:
            raise Exception("Could not find auto ph data in log file.")
        if starting_ph == -1.0:
            raise Exception("The first pH was not found in the log file.")
        if reagent_check == "unknown":
            raise Exception("Failed to get reagent check result.")

        # draw the plot
        image_name = "plot.png"
        image_path = os.path.join(output_path, image_name)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(x, y)
        ax.set_title("Initialization AutopH Profile")
        ax.set_xlabel("W1 added(ml)")
        ax.set_ylabel("W2 pH")
        fig.savefig(image_path, dpi=90)

        # generate the plot data stuff...
        if os.path.exists(image_path):
            html_handle.write("<p style=\"text-align:center;\">")
            html_handle.write("<img src=\"" + image_name + "\" />")
            html_handle.write("</p>")

        # write out raw init image tag
        if os.path.exists(os.path.join(archive_path, 'RawInit.jpg')):
            html_handle.write("<br />")
            html_handle.write("<h2 align=\"center\">Raw Init Plot</h2>")
            html_handle.write("<p style=\"text-align:center;\">")
            html_handle.write("<img src=\"../../RawInit.jpg\" />")
            html_handle.write("</p>")

        # write the raw traces
        html_handle.write("<br>")
        html_handle.write("<h2 align=\"center\">Reagent Check: {}</h2>".format(failure or reagent_check))
        if len(raw_traces) > 0:
            html_handle.write("<p style=\"text-align:center;\">")
            html_handle.write("<br />".join(raw_traces))
            html_handle.write("</p>")

        if failure:
            print_alert(failure)
        else:
            print_info("Starting pH: {} | W1 added (ml): {} | Reagent Check: {}".format(starting_ph, x[-1], reagent_check))
except Exception as exc:
    print_na(str(exc))
