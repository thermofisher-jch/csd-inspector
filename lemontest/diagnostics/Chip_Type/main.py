#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *


try:
    # get the path to the log file
    archive_path, output_path = sys.argv[1:3]
    data = read_explog(archive_path)
    print_info(get_chip_type_from_exp_log(data))

except Exception as exc:
    print_na(str(exc))


