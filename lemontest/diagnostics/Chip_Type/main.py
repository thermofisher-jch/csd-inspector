#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *


try:
    # get the path to the log file
    archive_path, output_path = sys.argv[1:3]
    data = read_explog(archive_path)
    chip_type = get_chip_type_from_exp_log(data)

    # get the chip efuse stuff
    if 'Chip Efuse' in data:
        chip_efuse = data['Chip Efuse'].split(',')
        l = chip_efuse[0].split(':')[1]
        w = chip_efuse[1].split(':')[1]
        chip_type += " | Lot " + l + "W" + w

    print_info(chip_type)

except Exception as exc:
    print_na(str(exc))


