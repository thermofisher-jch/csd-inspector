#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *

archive_path, output_path = sys.argv[1:3]

try:
    # get the path to the log file
    data = read_explog(archive_path)
    chip_type = get_chip_type_from_exp_log(data)

    # parse efuse line
    efuse_dict = {}
    for pair in data.get('Chip Efuse', '').split(','):
        if ":" in pair:
            key, value = pair.split(":")
            efuse_dict[key.strip()] = value.strip()

    if "L" in efuse_dict:
        chip_type += " | Lot " + efuse_dict["L"]

    if "W" in efuse_dict:
        chip_type += " | W " + efuse_dict["W"]

    print_info(chip_type)

except Exception as exc:
    handle_exception(exc, output_path)


