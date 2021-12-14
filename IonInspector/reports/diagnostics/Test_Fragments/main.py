#!/usr/bin/env python

import semver
import sys
import os.path
from reports.diagnostics.common.inspector_utils import *
from math import floor


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        # read the exp log
        exp_log = read_explog(archive_path)

        # special rule for TS < 5.0.5
        sw_version = get_ts_version(archive_path)

        if exp_log.get("LibKit") == "IonPicoPlex":
            if semver.match(sw_version, "<=5.0.5"):
                return print_na(
                    "TF's not reported for reproseq in TS 5.0.5 or earlier."
                )

        tf_stats_paths = [
            os.path.join(
                archive_path, "CSA", "outputs", "BaseCallingActor-00", "TFStats.json"
            ),
            os.path.join(archive_path, "basecaller_results", "TFStats.json"),
        ]
        for tf_stats_path in tf_stats_paths:
            if os.path.exists(tf_stats_path):
                break
        else:
            raise Exception(
                "TFStats.json file is missing so this test cannot be evaluated."
            )

        # read the tf stats
        with open(tf_stats_path, "r") as handle:
            tf_stats = json.load(handle)

        # iterate through all of the keys in the dictionary and look for test fragment information
        rates = list()
        for key in tf_stats.keys():
            if (
                key.startswith("TF_")
                and "50Q17" in tf_stats[key]
                and "Num" in tf_stats[key]
            ):
                percent = int(
                    floor(
                        100.0
                        * (float(tf_stats[key]["50Q17"]) / float(tf_stats[key]["Num"]))
                    )
                )
                rates.append(key + " - " + str(percent) + "%")

        # check that we got any test fragment information to report
        if len(rates) == 0:
            raise Exception(
                "Not enough TF's reported in thumbnail. Review full chip PDF for possible TF reads."
            )

        return print_info(" | ".join(rates))
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
