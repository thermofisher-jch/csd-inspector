#!/usr/bin/env python

from django.template import Context, Template
import json
from IonInspector.reports.diagnostics.common.inspector_utils import *
import numpy as np
import os
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        plt.text(rect.get_x()+rect.get_width()/2., 1.01 * height, '%d' % int(height), ha='center', va='bottom')


def get_param_sigproc(log, key):
    """This helper method will search the log for the key"""
    delimiter = ':'
    p = re.compile('^' + key + '\s*' + delimiter)
    for line in log:
        if p.match(line):
            try:
                return int(line.split(delimiter)[1].strip())
            except ValueError:
                raise Exception("Could not parse " + line)

    raise Exception("Could not find " + key + " in sigproc.log.")


def create_plot(plot_data, image_path):
    """helper for creating bar plots"""
    color_scheme = 'bgrcmykb'
    labels = plot_data.keys()
    y_pos = np.arange(len(labels))
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.bar(y_pos, plot_data.values(), align='center', alpha=0.5, color=color_scheme[:len(plot_data.keys())])
    ax.set_xticks(y_pos)
    ax.set_xticklabels(labels)
    ax.tick_params(top='off', right='off', bottom='off')
    ax.set_ylabel("Reads (1,000's)")
    ax.spines['right'].set_linewidth(0.0)
    ax.spines['top'].set_linewidth(0.0)
    autolabel(ax.patches)
    fig.tight_layout()

    fig.savefig(image_path)


def bar_value_to_header(value, total_values):
    """helper to put together bar titles"""
    return str(value) + '\n' + str(int(float(value) / float(total_values) * 100.0)) + '% of all'


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        font = {'family': 'sans-serif', 'weight': 'normal', 'size': 10}
        matplotlib.rc('font', **font)

        # check that this is a valid hardware set for evaluation
        explog = read_explog(archive_path)
        check_supported(explog)

        with open(os.path.join(archive_path, 'basecaller_results', 'BaseCaller.json')) as base_caller_handle:
            base_caller = json.load(base_caller_handle)

        quality_filter = base_caller.get('Filtering', dict()).get('ReadDetails', dict()).get('lib', dict()).get('quality_filter', 0)

        # get the information from the signal processing results
        sigproc_path = os.path.join(archive_path, 'sigproc_results', 'sigproc.log')
        if not os.path.exists(sigproc_path):
            raise Exception("Cannot find signal processing log or a thumbnail S5/Proton CSA was not uploaded.")

        sigproc_log = list()
        with open(sigproc_path) as sigproc_fp:
            sigproc_log = sigproc_fp.readlines()

        beads = get_param_sigproc(sigproc_log, "Beads")
        empties = get_param_sigproc(sigproc_log, "Empties")
        pinned = get_param_sigproc(sigproc_log, "Pinned")
        ignored = get_param_sigproc(sigproc_log, "Ignored")
        pwc_total = beads + empties + pinned + ignored
        create_plot({
            'Beads': beads/1000,
            'Empties': empties/1000,
            'Pinned': pinned/1000,
            'Ignored': ignored/1000,
        }, os.path.join(output_path, 'primary.png'))

        library = get_param_sigproc(sigproc_log, "Library")
        tfbead = get_param_sigproc(sigproc_log, "TFBead")
        duds = get_param_sigproc(sigproc_log, "Duds")

        create_plot({
            'Library': library/1000,
            'TFBead': tfbead/1000,
            'Duds': duds/1000,
        }, os.path.join(output_path, 'loaded.png'))

        basecaller_path = os.path.join(archive_path, 'basecaller_results', 'BaseCaller.json')
        if not os.path.exists(basecaller_path):
            raise Exception("Cannot find base caller log for thumbnail.")

        basecaller_log = dict()
        with open(basecaller_path) as basecaller_fp:
            basecaller_log = json.load(basecaller_fp)

        d = basecaller_log['Filtering']['ReadDetails']['lib']
        low_quality_high_ppf = int(d['bkgmodel_high_ppf'])
        polyclonal = int(d['bkgmodel_polyclonal'])
        low_quality_bad_key = int(d['bkgmodel_keypass'])
        low_quality_short_read = int(d['short'])
        low_quality_failed_keypass = int(d['failed_keypass'])
        primer_dimer = int(d['adapter_trim'])
        low_quality_quality_trim = int(d['quality_trim'])
        final_library_isps = int(d['valid'])

        data = {
            'Low\nQuality:\nHigh\nPPF':       low_quality_high_ppf / 1000,
            'Polyclonal': polyclonal/1000,
            'Low\nQuality:\nBad\nKey': low_quality_bad_key/1000,
            'Low\nQuality:\nShort\nRead': low_quality_short_read/1000,
            'Low\nQuality:\nFailed\nKeypass': low_quality_failed_keypass/1000,
            'Primer\nDimer': primer_dimer/1000,
            'Low\nQuality:\nQuality\nTrim': low_quality_quality_trim/1000,
            'Final\nLibrary\nISPs': final_library_isps/1000,
            'Quality\nFilter': quality_filter/1000,
        }
        create_plot(data, os.path.join(output_path, 'library.png'))

        write_results_from_template({
            'pwc_beads': beads, 'pwc_beads_perc': float(beads) / float(pwc_total) * 100.0,
            'pwc_empties': empties, 'pwc_empties_perc': float(empties) / float(pwc_total) * 100.0,
            'pwc_pinned': pinned, 'pwc_pinned_perc': float(pinned) / float(pwc_total) * 100.0,
            'pwc_ignored':                           ignored, 'pwc_ignored_perc': float(ignored) / float(pwc_total) * 100.0,
            'pwc_total':                             pwc_total,
            'loaded_library':                        library, 'loaded_library_perc': float(library) / float(beads) * 100.0,
            'loaded_tfbead':                         tfbead, 'loaded_tfbead_perc': float(tfbead) / float(beads) * 100.0,
            'loaded_duds':                           duds, 'loaded_duds_perc': float(duds) / float(beads) * 100.0,
            'libarary_low_quality_high_ppf':         low_quality_high_ppf, 'libarary_low_quality_high_ppf_prec': float(low_quality_high_ppf) / float(library) * 100.0,
            'libarary_polyclonal':                   polyclonal, 'libarary_polyclonal_perc': float(polyclonal) / float(library) * 100.0,
            'libarary_low_quality_bad_key':          low_quality_bad_key, 'libarary_low_quality_bad_key_perc': float(low_quality_bad_key) / float(library) * 100.0,
            'libarary_low_quality_short_read_key':   low_quality_short_read, 'libarary_low_quality_short_read_perc': float(low_quality_short_read) / float(library) * 100.0,
            'libarary_low_quality_failed_keypass':   low_quality_failed_keypass, 'libarary_low_quality_failed_keypass_perc': float(low_quality_failed_keypass) / float(library) * 100.0,
            'libarary_primer_dimer': primer_dimer, 'libarary_primer_dimer_perc': float(primer_dimer) / float(library) * 100.0,
            'libarary_low_quality_quality_trim': low_quality_quality_trim, 'libarary_low_quality_quality_trim_perc': float(low_quality_quality_trim) / float(library) * 100.0,
            'libarary_final_library_isps': final_library_isps, 'libarary_final_library_isps_perc': float(final_library_isps) / float(library) * 100.0,
            'quality_filter': quality_filter,
            'quality_filter_perc': float(quality_filter) / float(library) * 100.0,
        }, output_path, os.path.dirname(os.path.realpath(__file__)))
        matplotlib.pyplot.close("all")
        return print_info("See results for details.")
    except Exception as exc:
        return handle_exception(exc, output_path)

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
