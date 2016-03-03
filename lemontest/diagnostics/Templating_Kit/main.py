#!/usr/bin/env python

import json
import os
import sys
from lemontest.diagnostics.common.inspector_utils import *

try:
    # get the path to the log file
    archive_path, output_path = sys.argv[1:3]

    # read the ion params file
    params = dict()
    with open(os.path.join(archive_path, 'ion_params_00.json')) as params_file:
        params = json.load(params_file)

    # check if the key is present in the dictionary
    if 'plan' not in params and 'templatingKitName' not in params['plan']:
        raise Exception("The templating kit name was not recorded.")

    # print the templating name
    print_ok(params['plan']['templatingKitName'])

except Exception as exc:
    print_na(str(exc))
