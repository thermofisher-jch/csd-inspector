#!/usr/bin/env python

import sys
from subprocess import check_output, Popen, PIPE
from lemontest.diagnostics.common.inspector_utils import *


archive_path, output_path, archive_type = sys.argv[1:4]
try:
    # check that this is a valid hardware set for evaluation
    explog = read_explog(archive_path)
    check_supported(explog)

    working_dir = os.path.dirname(__file__)
    r_script_path = os.path.join(working_dir, 'filter_metrics.R')
    command = "Rscript"
    args = [archive_path, output_path]
    cmd = [command, r_script_path] + args
    check_output(cmd, cwd=working_dir, universal_newlines=True)
    print_info("See results for details.")
except Exception as exc:
    handle_exception(exc, output_path)
