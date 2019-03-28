import json
import ConfigParser
import os
from collections import defaultdict

ARCHIVE_PATH = ".local/media/archive_files/14/"


def lib_wells_from_analysis_bfmask_stats(path):
    config = ConfigParser.RawConfigParser()
    config.read(path)
    return config.getint("global", "library beads")

totals = defaultdict(int)

def lib_wells_from_base_caller_json(path):
    wells = 0
    with open(path) as fp:
        lib = json.load(fp)["Filtering"]["ReadDetails"]["lib"]
        for key, value in lib.items():
            if type(value) is int:
                totals[key] += value
                wells += value
    return wells


def check_match(a, b):
    if a == b:
        print("\033[1;32;40m{} {}\033[0m".format(a, b))
    else:
        print("\033[1;31;40m{} {}\033[0m".format(a, b))


assay_wells_base_caller_total = 0
assay_wells_bfmask_total = 0

# Try per block
for folder in os.listdir(ARCHIVE_PATH + "CSA/outputs/BaseCallingActor-00/"):
    if folder.startswith("block_"):
        assay_wells_base_caller = lib_wells_from_base_caller_json(
            ARCHIVE_PATH + "CSA/outputs/BaseCallingActor-00/{}/BaseCaller.json".format(folder))
        assay_wells_base_caller_total += assay_wells_base_caller

        assay_wells_bfmask = lib_wells_from_analysis_bfmask_stats(
            ARCHIVE_PATH + "CSA/outputs/SigProcActor-00/{}/analysis.bfmask.stats".format(folder))
        assay_wells_bfmask_total += assay_wells_bfmask

        print("Block {}:".format(folder)),
        check_match(assay_wells_base_caller, assay_wells_bfmask)

for key, value in totals.items():
    print key, value

print("Block Totals:"),
check_match(assay_wells_base_caller_total, assay_wells_bfmask_total)


assay_wells_base_caller = lib_wells_from_base_caller_json(
    ARCHIVE_PATH + "CSA/outputs/BaseCallingActor-00/BaseCaller.json")
assay_wells_bfmask = lib_wells_from_analysis_bfmask_stats(
    ARCHIVE_PATH + "CSA/outputs/SigProcActor-00/analysis.bfmask.stats")


print("Merged Files:"),
check_match(assay_wells_base_caller, assay_wells_bfmask)
