#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import sys
from lemontest.diagnostics.common.inspector_utils import *


try:
    archive_path, output_path = sys.argv[1:3]

    # read the ion params file
    params = dict()
    with open(os.path.join(archive_path, 'ion_params_00.json')) as params_file:
        params = json.load(params_file)

    # check if the key is present in the dictionary
    if 'plan' not in params and 'templatingKitName' not in params['plan']:
        raise Exception("The templating kit name was not recorded.")

    # get the sequencing kit description from the exp log
    exp_log = read_explog(archive_path)
    inspector_seq_kit = exp_log.get("SeqKitDesc", None) or exp_log.get("SeqKitPlanDesc", None)
    if not inspector_seq_kit:
        raise Exception("Seq Kit missing from explog_final.txt")

    print_info("Sequencing Kit: <b>" + inspector_seq_kit + "</b> | Templating Kit Name: <b>" + params['plan']['templatingKitName'] + "</b>")

except Exception as exc:
    print_na(str(exc))
