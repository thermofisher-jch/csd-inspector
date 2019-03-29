#!/usr/bin/env python

import sys
from IonInspector.reports.diagnostics.common.inspector_utils import *
from dateutil.parser import parse
from datetime import date

ASSEMBLY = {"D": "Tong Hsing"}

PRODUCT = {"A": "RUO", "X": "Dx"}


def parse_efuse(value):
    values = {}

    # raw values
    for chunk in value.split(","):
        if ":" in chunk:
            k, v = chunk.split(":", 1)
            values[k] = v

    # extra values
    values["Assembly"] = ASSEMBLY[values["BC"][2]]
    values["Product"] = PRODUCT[values["BC"][3]]

    values["ExpirationYear"] = ord(values["BC"][4]) - ord("A") + 2015
    values["ExpirationMonth"] = ord(values["BC"][5]) - ord("A") + 1

    return values


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        # get the path to the log file
        explog = read_explog(archive_path)

        efuse = parse_efuse(explog["Chip Efuse"])

        run_date = parse(explog.get('Start Time', 'Unknown')).replace(day=1).date()
        exp_date = date(efuse["ExpirationYear"], efuse["ExpirationMonth"], 1)

        message = "{} | L {} | W {} | Assembled {} | Expiration {}".format(
            efuse["CT"],
            efuse["L"],
            efuse["W"],
            efuse["Assembly"],
            exp_date.strftime("%b %Y"))

        if run_date > exp_date:
            return print_alert(message + " EXPIRED!")
        else:
            return print_info(message)

    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
