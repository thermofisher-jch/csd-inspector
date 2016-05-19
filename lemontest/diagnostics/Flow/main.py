#!/usr/bin/env python

import csv
import sys
import os.path
from mako.template import Template
from lemontest.diagnostics.common.inspector_utils import *

# constants
TIMESTAMP = 'timestamp'
TACK_FLOW = 'tach_flow'

try:
    # in order to generate plots without a display this "magic" Agg parameter must be passed to the module
    # before your import pyplot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    archive, output = sys.argv[1:3]

    # read the data in from the csv into a dictionary of lists keyed by header column name
    csv = get_csv_from_run_log(archive)

    # check that there is data
    if len(csv[TIMESTAMP]) == 0 or len(csv[TACK_FLOW]) == 0:
        raise Exception('No data in the csv to plot.')

    # generate the plot for rendering
    plt.plot(csv[TIMESTAMP], csv[TACK_FLOW])
    plt.title("Ion Chef Liquid Cooling: Flowmeter")
    plt.xlabel("Time (sec)")
    plt.ylabel("Flow Rate (Hz)")
    figure_path = os.path.join(output, "plot.png")
    plt.savefig(figure_path, dpi=90)

    # write out the html resutls
    template = Template(filename="logs.mako")
    result = template.render(**dict())
    with open(os.path.join(output, "results.html"), 'w') as out:
        out.write(result.encode("UTF-8"))

    print_info("Liquid cooling flowmeter.")
except Exception as exc:
    print_na(str(exc))
