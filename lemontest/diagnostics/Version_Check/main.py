#!/usr/bin/env python

import sys
import os


version_threshold = '3.0'

proton_version = 'Proton Release'
pgm_version    = 'PGM SW Release'

def load_explog(path):
    data = {}
    for line in open(path):
        # Trying extra hard to accomodate formatting issues in explog
        datum = line.split(": ", 1)
        if len(datum) == 2:
            key, value = datum
            data[key.strip()] = value.strip()
    return data


def validate(archive_path):
    path = os.path.join(archive_path, "explog_final.txt")
    if not os.path.exists(path):
        return "explog_final.txt missing", False

    explog = load_explog(path)
    if pgm_version not in explog and proton_version not in explog:
        return "Instrument version missing from explog_final.txt", False

    return explog, True


if __name__ == "__main__":
    outpath = sys.argv[1]
    version_path = os.path.join(outpath, "version.txt")
    if os.path.exists(version_path):
        line = open(version_path).readline()
        version = line.split('=')[-1].strip()
        if version >= version_threshold:
            print("OK")
            print("10")
            print("TS Version is acceptable at <strong>%s</strong>" % version)
        else:
            print("Alert")
            print("40")
            print("Advise customer to upgrade their Torrent Server.  Their version is out-dated at <strong>%s</strong>" % version)
        data, valid = validate(outpath)
        if valid:
            version = data.get(pgm_version, None) or data.get(proton_version, None)
            if version:
                print("  Instrument version is <strong>%s</strong>" % version)
    else:
        print("N/A")
        print("0")
        print("No version.txt included")
