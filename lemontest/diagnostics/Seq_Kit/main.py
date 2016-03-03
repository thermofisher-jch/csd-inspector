#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from lemontest.diagnostics.common.inspector_utils import *


def load_explog(path):
    data = {}
    for line in open(path):
        # Trying extra hard to accomodate formatting issues in explog
        datum = line.split(":", 1)
        if len(datum) == 2:
            key, value = datum
            data[key.strip()] = value.strip()
    return data


def validate(archive_path):
    explog = read_explog(archive_path)
    data = {}
    data['inspector_seq_kit'] = explog.get("SeqKitDesc", None)
    if not data['inspector_seq_kit']:
        data['inspector_seq_kit'] = explog.get("SeqKitPlanDesc", None)
        if not data['inspector_seq_kit']:
            return "Seq Kit missing from explog_final.txt", data, False
    return explog, data, True


def report(data):
    kit_name = data.get("inspector_seq_kit")
    if "IC" in kit_name:
        print("Info")
        print(20)
        print(u"Chef kit, {}".format(kit_name))
    else:
        print("Info")
        print(20)
        print(u"OneTouch kit, {}".format(kit_name))
        

def main():
    archive_path, output_path = sys.argv[1:3]
    raw, data, valid = validate(archive_path)
    if not valid:
        print("N\A")
        print(0)
        print(raw)
        sys.exit()
    else:
        report(data)

main()
