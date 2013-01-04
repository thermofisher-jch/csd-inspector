#!/usr/bin/env python

import sys
import os


version_threshold = '3.0'

if __name__ == "__main__":
    outpath = sys.argv[1]
    version_path = os.path.join(outpath, "version.txt")
    if os.path.exists(version_path):
        line = open(version_path).readline()
        version = line.split('=')[-1].strip()
        if version >= version_threshold:
            print("OK")
            print("10")
            print("Version is acceptable at %s" % version)
        else:
            print("Fail")
            print("40")
            print("Advise customer to upgrade their Torrent Server.  Their version is out-dated at %s" % version)
    else:
        print("N/A")
        print("0")
        print("No version.txt included")
