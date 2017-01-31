#!/usr/bin/env python

from django.template import Context, Template
import json
from lemontest.diagnostics.common.inspector_utils import *
import numpy as np
import os
import re
from subprocess import check_output, Popen, PIPE
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        plt.text(rect.get_x()+rect.get_width()/2., 1.01 * height, '%d' % int(height), ha='center', va='bottom')


def get_param_sigproc(log, key, delimiter):
    """This helper method will search the log for the key"""

    p = re.compile('^' + key + '\s*' + delimiter)
    for line in log:
        if p.match(line):
            try:
                return int(line.split(delimiter)[1].strip())/1000
            except ValueError:
                raise Exception("Could not parse " + line)

    raise Exception("Could not find " + key + " in sigproc.log.")


def create_plot(data, title, image_path):
    """helper for creating bar plots"""

    labels = data.keys()
    y_pos = np.arange(len(labels))
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.bar(y_pos, data.values(), align='center', alpha=0.5)
    ax.set_title(title)
    ax.set_xticks(y_pos)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Reads (1,000's)")
    autolabel(ax.patches)
    fig.savefig(image_path)


archive_path, output_path, archive_type = sys.argv[1:4]
try:
    font = {'family': 'sans-serif', 'weight': 'normal', 'size': 10}
    matplotlib.rc('font', **font)

    # check that this is a valid hardware set for evaluation
    explog = read_explog(archive_path)
    check_supported(explog)

    # get the information from the signal processing results
    sigproc_path = os.path.join(archive_path, 'sigproc_results', 'sigproc.log')
    if not os.path.exists(sigproc_path):
        raise Exception("Cannot find signal processing log for thumbnail.")

    sigproc_log = list()
    with open(sigproc_path) as sigproc_fp:
        sigproc_log = sigproc_fp.readlines()

    create_plot({
        'Beads': get_param_sigproc(sigproc_log, "Beads", ":"),
        'Empties': get_param_sigproc(sigproc_log, "Empties", ":"),
        'Pinned': get_param_sigproc(sigproc_log, "Pinned", ":"),
        'Ignored': get_param_sigproc(sigproc_log, "Ignored", ":"),
    }, "Primary Well Categorization", os.path.join(output_path, 'primary.png'))

    create_plot({
        'Library': get_param_sigproc(sigproc_log, "Library", ":"),
        'TFBead': get_param_sigproc(sigproc_log, "TFBead", ":"),
        'Duds': get_param_sigproc(sigproc_log, "Duds", ":")
    }, 'Loaded Well Categorization', os.path.join(output_path, 'loaded.png'))

    basecaller_path = os.path.join(archive_path, 'basecaller_results', 'BaseCaller.json')
    if not os.path.exists(basecaller_path):
        raise Exception("Cannot find base caller log for thumbnail.")

    basecaller_log = dict()
    with open(basecaller_path) as basecaller_fp:
        basecaller_log = json.load(basecaller_fp)

    d = basecaller_log['Filtering']['ReadDetails']['lib']
    data = {
        'Low\nQuality:\nHigh\nPPF': int(d['bkgmodel_high_ppf'])/1000,
        'Polyclonal': int(d['bkgmodel_polyclonal'])/1000,
        'Low\nQuality:\nBad\nKey': int(d['bkgmodel_keypass'])/1000,
        'Low\nQuality:\nShort\nRead': int(d['short'])/1000,
        'Low\nQuality:\nFailed\nKeypass': int(d['failed_keypass'])/1000,
        'Primer\nDimer': int(d['adapter_trim'])/1000,
        'Low\nQuality:\nQuality\nTrim': int(d['quality_trim'])/1000,
        'Final\nLibrary\nISPs': int(d['valid'])/1000,
    }
    create_plot(data, "Filter Metrics Plots", os.path.join(output_path, 'library.png'))

    template = Template(open("results.html").read())
    result = template.render(Context())
    with open(os.path.join(output_path, "results.html"), 'w') as out:
        out.write(result.encode("UTF-8"))

    print_ok("See results")
except Exception as exc:
    handle_exception(exc, output_path)
