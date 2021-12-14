#!/usr/bin/env python

import os
import re
import sys
from reports.diagnostics.common.inspector_utils import *

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    results_path = os.path.join(output_path, "results.html")
    try:
        # data to be populated
        failure = ""
        starting_ph = -1.0
        reagent_check = "unknown"
        raw_traces = list()
        x = list()
        y = list()

        # get the paths

        init_log_path = os.path.join(archive_path, "InitLog.txt")
        if not os.path.exists(init_log_path):
            raise Exception("InitLog.txt is not present so test cannot be run.")

        # read in the init log lines
        init_log = list()
        with open(init_log_path, "r") as init_log_handle:
            init_log = init_log_handle.readlines()

        # TODO: perhaps move this to a template
        with open(results_path, "w") as html_handle:
            html_handle.write(
                "<html><link rel=stylesheet href=some.css type=text/css>\n"
            )
            html_handle.write("</head><body>")
            html_handle.write('<h1 align="center">AutopH plot</h1>')

            if "Proton" == archive_type:
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
                        starting_ph = float(line.split("=")[1])
                    elif line.startswith("Rawtrace:"):
                        reagent_check = line.split(": ")[1]
                    elif re.search("[WR]\dpH", line):
                        raw_traces.append(line.strip())

            else:
                # gather up all of the steps reported in the log and organize them according to their step number
                step_lines = dict()
                for line in init_log:
                    if re.search("^\d+\)", line):
                        line_split = line.split(")", 1)
                        step_number = int(line_split[0])
                        step_line = line_split[1].strip()
                        if step_number not in step_lines:
                            step_lines[step_number] = dict()
                        if step_line.startswith("W2"):
                            step_lines[step_number]["W2"] = float(
                                step_line.split("=", 1)[1]
                            )
                        if step_line.startswith("Adding"):
                            step_lines[step_number]["Adding"] = float(
                                step_line.split(" ")[1]
                            )
                    elif line.startswith("FAILEDUNDERSHOT"):
                        failure = "Undershot the pH."
                    elif line.startswith("RawTraces:"):
                        reagent_check = line.split(": ")[1]
                    elif line.startswith("RawTraces "):
                        raw_traces.append(line.split(" ", 1)[1])

                starting_ph = float(step_lines[1]["W2"])

                # parse the lines for information
                for step_number in step_lines.keys():
                    step_values = step_lines[step_number]
                    if "W2" in step_values:
                        volume_added = 0
                        for i in range(step_number):
                            volume_added += step_lines[i + 1].get("Adding", 0.0)
                        x.append(volume_added)
                        y.append(step_values["W2"])

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
                html_handle.write('<p style="text-align:center;">')
                html_handle.write('<img src="' + image_name + '" />')
                html_handle.write("</p>")

            # write out raw init image tag
            if os.path.exists(os.path.join(archive_path, "RawInit.jpg")):
                html_handle.write("<br />")
                html_handle.write('<h2 align="center">Raw Init Plot</h2>')
                html_handle.write('<p style="text-align:center;">')
                html_handle.write('<img src="../../RawInit.jpg" />')
                html_handle.write("</p>")
            elif os.path.exists(os.path.join(archive_path, "InitRawTrace0.png")):
                html_handle.write("<br />")
                html_handle.write('<h2 align="center">Raw Init Plot</h2>')
                html_handle.write('<p style="text-align:center;">')
                html_handle.write('<img src="../../InitRawTrace0.png" />')
                html_handle.write("</p>")

            # write the raw traces
            html_handle.write("<br>")
            html_handle.write(
                '<h2 align="center">Reagent Check: {}</h2>'.format(
                    failure or reagent_check
                )
            )
            if len(raw_traces) > 0:
                html_handle.write('<p style="text-align:center;">')
                html_handle.write("<br />".join(raw_traces))
                html_handle.write("</p>")

            matplotlib.pyplot.close("all")

            if failure:
                return print_failed(failure)
            else:
                return print_info(
                    "Starting pH: {} | W1 added (ml): {} | Reagent Check: {}".format(
                        starting_ph, x[-1], reagent_check
                    )
                )
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
