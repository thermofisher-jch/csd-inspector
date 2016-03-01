#!/usr/bin/env python

import sys
import os
from distutils.version import StrictVersion
from inspector_utils import *

OK_STRING = "TS Version is acceptable at <strong>%s</strong>"
ALERT_STRING = "Advise customer to upgrade their Torrent Server.  Their version is out-dated at <strong>%s</strong>"


def validate(archive_path):
    explog = read_explog(archive_path)
    return explog, True


def printResult(alert, msg):
    """
    Helper method to print the alert statement
    :param alert: boolean if this is an alert
    :param msg: The message to be printed
    """
    print("Alert" if alert else "OK")
    print("40" if alert else "10")
    print(msg)

if __name__ == "__main__":
    outpath = sys.argv[1]
    explog, valid = validate(outpath)
    if not valid:
        print("N/A")
        print("0")
        print "Could not find a valid explog."
        exit()

    version_path = os.path.join(outpath, "version.txt")
    if not os.path.exists(version_path):
        print("N/A")
        print("0")
        print("No version.txt included")
        exit()

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


