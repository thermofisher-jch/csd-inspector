#!/usr/bin/env python

import sys
from datetime import date

from dateutil.parser import parse

from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_alert,
    print_info,
    read_explog,
    get_chip_type_from_exp_log,
)

ASSEMBLY = {"D": "Tong Hsing"}

PRODUCT = {"A": "RUO", "X": "Dx"}


def parse_efuse(value):
    values = {}

    # if empty or None, return empty dict
    if not value:
        return values

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

    # get the path to the log file, read with special parser
    # and return with explog dict
    explog = read_explog(archive_path)

    efuse = parse_efuse(explog.get("Chip Efuse", ""))

    # PGM explog.txt does not have Chip Efuse field
    if not efuse:
        chip_type = get_chip_type_from_exp_log(explog)
        return print_info(chip_type)

    run_date = parse(explog.get("Start Time", "Unknown")).replace(day=1).date()
    exp_date = date(efuse["ExpirationYear"], efuse["ExpirationMonth"], 1)

    message = "{chip_type} | L {lot_info} | W {wafer_info} | Expiration {exp_date_str}".format(
        chip_type=efuse["CT"],
        lot_info=efuse["L"],
        wafer_info=efuse["W"],
        exp_date_str=exp_date.strftime("%b %Y"),
    )

    if run_date > exp_date:
        return print_alert(message + " EXPIRED!")
    else:
        return print_info(message)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
