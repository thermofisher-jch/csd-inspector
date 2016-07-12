#!/usr/bin/env python

import sys
import os
from distutils.version import StrictVersion
from lemontest.diagnostics.common.inspector_utils import *

OK_STRING = "TS Version is acceptable at <strong>%s</strong>"
ALERT_STRING = "Advise customer to upgrade their Torrent Server.  Their version is out-dated at <strong>%s</strong>"


def printResult(alert, msg):
    """
    Helper method to print the alert statement
    :param alert: boolean if this is an alert
    :param msg: The message to be printed
    """
    print("Alert" if alert else "OK")
    print("40" if alert else "10")
    print(msg)

archive_path, output_path, archive_type = sys.argv[1:4]
try:
    # check that this is a valid hardware set for evaluation
    explog = read_explog(archive_path)
    check_supported(explog)
    version_path = os.path.join(output_path, "version.txt")
    if not os.path.exists(version_path):
        raise Exception("Missing file: " + version_path)

    # get the version number
    line = open(version_path).readline()
    version = line.split('=')[-1].strip()
    version = version.split()[0]

    if "S5 Release_version" in explog:
        # version check for S5 XL
        if explog['SystemType'] == 'S5XL':
            if StrictVersion(version) >= StrictVersion('5.0'):
                printResult(False, OK_STRING % version)
            else:
                printResult(True, ALERT_STRING % version)
        # version check for S5
        if explog['SystemType'] == 'S5':
            if StrictVersion(version) >= StrictVersion('5.0.2'):
                printResult(False, OK_STRING % version)
            else:
                printResult(True, ALERT_STRING % version)

    # version check for PGM
    elif "PGM SW Release" in explog:
        if StrictVersion(version) >= StrictVersion('4.6'):
            printResult(False, OK_STRING % version)
        else:
            printResult(True, ALERT_STRING % version)
    # fallback version check
    else:
        if version:
            printResult(False, OK_STRING % version)
        else:
            printResult(True, "Could not get a valid version to check against.")
except Exception as exc:
    handle_exception(exc, output_path)

