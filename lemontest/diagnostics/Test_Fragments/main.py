#!/usr/bin/env python

import json
import sys
import os.path
from lemontest.diagnostics.common.inspector_utils import *
from math import floor

try:
    archive_path, output_path = sys.argv[1:3]
    tf_stats_path = os.path.join(archive_path, 'basecaller_results', 'TFStats.json')
    if not os.path.exists(tf_stats_path):
        raise Exception("TFStats.json file is missing so this test cannot be evaluated.")

    # read the tf stats
    tf_stats = dict()
    with open(tf_stats_path, 'r') as handle:
        tf_stats = json.load(handle)

    # iterate through all of the keys in the dictionary and look for test fragment information
    rates = list()
    for key in tf_stats.keys():
        if key.startswith('TF_') and "50Q17" in tf_stats[key] and "Num" in tf_stats[key]:
            percent = int(floor(100.0 * (float(tf_stats[key]["50Q17"]) / float(tf_stats[key]["Num"]))))
            rates.append(key + " - " + str(percent) + "%")

    # check that we got any test fragment information to report
    if len(rates) == 0:
        raise Exception("Could not find any test framgents in the TF Stats file.")

    print_info(" | ".join(rates))
except Exception as exc:
    print_na(str(exc))
