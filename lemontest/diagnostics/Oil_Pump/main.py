#!/usr/bin/env python

import csv
import sys
import os.path

COLUMN_HEADER = "Oil Pump Status"

normal_operation = {
    0: ["Ready/Idle state", "Pump operating normally"],
    22: ["Busy", "Pump operating normally"],
}

error_codes = {
    1: ("Error during initialization", "Error not documented - No Instruction"),
    2: ("Invalid command", "Power cycle instrument"),
    3: ("Invalid operand", "Error not documented - No Instruction"),
    4: ("Invalid command sequence", "Error not documented - No Instruction"),
    5: ("Pump not initialized", "Power cycle instrument"),
    9: ("Plunger overload", "Error not documented - No Instruction"),
    10: ("Valve overload", "Error not documented - No Instruction"),
    11: ("Move not allowed", "Error not documented - No Instruction"),
    15: ("Command overflow", "Error not documented - No Instruction"),
    16: ("Read timeout", "Error not documented - No Instruction"),
    17: ("Write timeout", "Error not documented - No Instruction"),
    18: ("Unknown error", "Error not documented - No Instruction"),
    19: ("Invalid format", "Error not documented - No Instruction"),
    20: ("Invalid param", "Error not documented - No Instruction"),
    21: ("Rs232 port not open", "Error not documented - No Instruction"),
    23: ("App wait timeout", "Error not documented - No Instruction"),
    24: ("No acknowledgement", "Error not documented - No Instruction"),
}

archive, output = sys.argv[1:3]
path = os.path.join(archive, "onetouch.log")
log = open(path)
# The first line is not actually part of the CSV, chuck it
log.readline()
reader = csv.reader(log)
headers = reader.next()
for index, header in enumerate(headers):
    if COLUMN_HEADER in header:
        break
else:
    print("N\A")
    print("0")
    print("Could not find Sample Pump Status column")
    sys.exit()

columns = [int(l[index]) for l in reader if l[index].isdigit()]
codes = set(columns)
errors = codes - set(normal_operation.keys())
unknown =  errors - set(error_codes.keys())

if not errors:
    print("OK")
    print("10")
else:
    print("Alert")
    print("40")
    print("<br/>\n".join("%s: %s" % (error_codes[e]) for e in sorted(errors)))
