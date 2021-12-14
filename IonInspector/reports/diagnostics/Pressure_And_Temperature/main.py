#!/usr/bin/env python

import collections
import json
import os
import sys

from reports.diagnostics.common.inspector_utils import (
    write_results_from_template,
    read_explog,
    get_explog_path,
    print_warning,
    print_alert,
    print_info,
)

INFO = 0
WARN = 1
ALARM = 2

PRESSURE_LIMITS = {
    "PGM_Run": {
        "keys": ["pressure"],
        "ranges": [(9.5, 11, "Pressure is low", "Pressure is high", ALARM)],
    },
    "Proton": {
        "keys": ["manifoldPressure", "regulatorPressure"],
        "ranges": [
            (10.0, 11.0, "Pressure is very low", "Pressure is very high", ALARM),
            (10.2, 10.8, "Pressure is low", "Pressure is high", WARN),
        ],
    },
    "S5": {
        "keys": ["manifoldPressure", "regulatorPressure"],
        "ranges": [(7.2, 8.8, "Pressure is low", "Pressure is high", ALARM)],
    },
    "Valkyrie": {
        "keys": ["manifoldPressure", "regulatorPressure"],
        "ranges": [(9.5, 10, "Pressure is low", "Pressure is high", ALARM)],
    },
}

TEMP_LIMITS = {
    "PGM_Run": {
        "keys": ["internalTemperature"],
        "ranges": [
            (26, 34, "Temperature is cold", "Temperature is hot", ALARM),
        ],
    },
    "Proton": {
        "keys": ["chipBayTemperature", "ambientTemperature", "ambientWasteTemperature"],
        "ranges": [
            (20, 34, "Temperature is cold", "Temperature is hot", ALARM),
        ],
    },
    "S5": {
        "keys": ["wasteTemperature", "ambientTemperature", "manifoldTemperature"],
        "ranges": [
            (20, 35, "Temperature is cold", "Temperature is hot", ALARM),
        ],
    },
    "Valkyrie": {
        "keys": ["wasteTemperature", "ambientTemperature"],
        "ranges": [
            (20, 35, "Temperature is cold", "Temperature is hot", ALARM),
        ],
    },
}


class OutOfRangeError(Exception):
    def __init__(self, message, level):
        self.message = message
        self.level = level


def validate_data_within_limits(values, limit, start_at_flow=0):
    for key in limit["keys"]:
        for range in limit["ranges"]:
            lower_bound, upper_bound, lower_message, upper_message, level = range
            for flow, y in values[key]["data"][start_at_flow:]:
                if y > upper_bound:
                    e = OutOfRangeError(
                        upper_message + " (%.2f) at flow %i" % (y, flow), level
                    )
                    raise e
                if y < lower_bound:
                    e = OutOfRangeError(
                        lower_message + " (%.2f) at flow %i" % (y, flow), level
                    )
                    raise e


# Shared parser. Used by proton and s5 to parse some strange log lines
def parse_experiment_info_log_line(line):
    """ExperimentInfoLog: is in a very odd format with line like
    acq_0272.dat: Pressure=7.91 7.95 Temp=39.99 31.19 30.01 26.64 dac_start_sig=1724
    """
    if ":" not in line:
        raise ValueError("Could not parse explog line: {}".format(line))
    dat_meta = collections.OrderedDict()
    dat_name, dat_meta_string = line.strip().split(":", 1)
    for token in dat_meta_string.strip().split(" "):
        if (
            "=" in token
        ):  # After tokenizing by spaces, some token are values, and some are keys and values
            key, value = token.split("=")
            dat_meta[key] = [value]
        else:  # If there is no = this token is a value
            dat_meta[dat_meta.keys()[-1]].append(token)
    return dat_name.strip(), dat_meta


def get_pressure_and_temp(archive_path, archive_type):
    """Executes the test"""
    exp_log_file_path = get_explog_path(archive_path)
    explog = read_explog(archive_path)

    # PGM Parsing
    def parse_flow_data_pgm(fp, new_pgm_format):
        # Flot friendly format
        data = {
            "pressure": {
                "pressure": {"data": [], "label": "Pressure"},
            },
            "temperature": {
                "internalTemperature": {"data": [], "label": "Internal Temperature"},
                "chipTemperature": {"data": [], "label": "Chip Temperature"},
            },
        }
        if new_pgm_format:  # PGM 1.1
            data["temperature"]["restrictorTemperature"] = {
                "data": [],
                "label": "Restrictor Temperature",
            }
            data["temperature"]["chipHeatsinkTemperature"] = {
                "data": [],
                "label": "Chip Heatsink Temperature",
            }

        reached_target_section = False
        flow_count = 0
        for line in fp:
            if line.startswith("Flow # Pressure"):
                reached_target_section = True
            elif reached_target_section and len(line) > 1:
                # Now we have a line we want
                dat_meta = line.strip().split()
                # Now we need to coerce some values
                if new_pgm_format:  # PGM 1.1
                    data["pressure"]["pressure"]["data"].append(
                        [flow_count, float(dat_meta[1])]
                    )
                    data["temperature"]["internalTemperature"]["data"].append(
                        [flow_count, float(dat_meta[2])]
                    )
                    data["temperature"]["restrictorTemperature"]["data"].append(
                        [flow_count, float(dat_meta[3])]
                    )
                    data["temperature"]["chipHeatsinkTemperature"]["data"].append(
                        [flow_count, float(dat_meta[4])]
                    )
                    data["temperature"]["chipTemperature"]["data"].append(
                        [flow_count, float(dat_meta[5])]
                    )
                else:  # PGM 1.0
                    data["pressure"]["pressure"]["data"].append(
                        [flow_count, float(dat_meta[1])]
                    )
                    data["temperature"]["internalTemperature"]["data"].append(
                        [flow_count, float(dat_meta[2])]
                    )
                    data["temperature"]["chipTemperature"]["data"].append(
                        [flow_count, float(dat_meta[3])]
                    )
                flow_count += 1
        return data

    # Proton Parsing
    def parse_flow_data_proton(fp):
        # Flot friendly format
        data = {
            "flowTypes": {},
            "pressure": {
                "manifoldPressure": {"data": [], "label": "Manifold Pressure"},
                "regulatorPressure": {"data": [], "label": "Regulator Pressure"},
            },
            "temperature": {
                "chipBayTemperature": {"data": [], "label": "Chip Bay Temperature"},
                "ambientTemperature": {"data": [], "label": "Ambient Temperature"},
                "ambientWasteTemperature": {
                    "data": [],
                    "label": "Ambient Waste Temperature",
                },
                "chipTemperature": {"data": [], "label": "Chip Temperature"},
            },
        }
        reached_target_section = False
        flow_count = 0
        last_flow_type = None
        for line in fp:
            if line.startswith("ExperimentInfoLog:"):
                reached_target_section = True
            elif line.startswith("ExperimentErrorLog:"):
                break
            elif reached_target_section and len(line) > 1:
                # Now we have a line we want
                dat_name, dat_meta = parse_experiment_info_log_line(line)
                # Now we need to coerce some values
                data["pressure"]["manifoldPressure"]["data"].append(
                    [flow_count, float(dat_meta["Pressure"][1])]
                )
                data["pressure"]["regulatorPressure"]["data"].append(
                    [flow_count, float(dat_meta["Pressure"][0])]
                )
                # https://stash.amer.thermo.com/projects/TS/repos/rndplugins/browse/autoCal/autoCal.R
                # 'Chip Bay','Ambient','Under Chip'
                data["temperature"]["chipBayTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][0])]
                )
                data["temperature"]["ambientTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][1])]
                )
                data["temperature"]["ambientWasteTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][3])]
                )
                # Chip temp
                data["temperature"]["chipTemperature"]["data"].append(
                    [flow_count, float(dat_meta["chipTemp"][0])]
                )
                # Track flow types
                if dat_name:
                    flow_type, _ = dat_name.rsplit("_", 1)
                    if flow_type != last_flow_type:
                        # Flow type has switched. Record the end of this flow type
                        if last_flow_type in data["flowTypes"]:
                            data["flowTypes"][last_flow_type]["end"] = flow_count - 1
                        # Create a new record for this flow type
                        data["flowTypes"][flow_type] = {
                            "start": flow_count,
                            "end": None,
                        }
                        last_flow_type = flow_type
                flow_count += 1
        # Add an endpoint for the acq flows
        data["flowTypes"][last_flow_type]["end"] = flow_count
        return data

    # S5 Parsing
    def parse_flow_data_s5(fp):
        # Flot friendly format
        data = {
            "flowTypes": {},
            "pressure": {
                "manifoldPressure": {"data": [], "label": "Manifold Pressure"},
                "regulatorPressure": {"data": [], "label": "Regulator Pressure"},
            },
            "temperature": {
                "manifoldHeaterTemperature": {
                    "data": [],
                    "label": "Manifold Heater Temperature",
                },
                "wasteTemperature": {"data": [], "label": "Waste Temperature"},
                "tecTemperature": {"data": [], "label": "TEC Temperature"},
                "ambientTemperature": {"data": [], "label": "Ambient Temperature"},
                "chipTemperature": {"data": [], "label": "Chip Temperature"},
                "manifoldTemperature": {"data": [], "label": "Manifold Temperature"},
            },
        }
        reached_target_section = False
        flow_count = 0
        last_flow_type = None
        for line in fp:
            if line.startswith("ExperimentInfoLog:"):
                reached_target_section = True
            elif line.startswith("ExperimentErrorLog:"):
                break
            elif reached_target_section and len(line) > 1:
                # Now we have a line we want
                dat_name, dat_meta = parse_experiment_info_log_line(line)
                # Now we need to coerce some values
                data["pressure"]["manifoldPressure"]["data"].append(
                    [flow_count, float(dat_meta["Pressure"][1])]
                )
                data["pressure"]["regulatorPressure"]["data"].append(
                    [flow_count, float(dat_meta["Pressure"][0])]
                )

                data["temperature"]["manifoldHeaterTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][0])]
                )
                data["temperature"]["wasteTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][1])]
                )
                data["temperature"]["tecTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][2])]
                )
                data["temperature"]["ambientTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][3])]
                )
                # Chip temp
                data["temperature"]["chipTemperature"]["data"].append(
                    [flow_count, float(dat_meta["chipTemp"][0])]
                )
                # Man temp
                data["temperature"]["manifoldTemperature"]["data"].append(
                    [flow_count, float(dat_meta["ManTemp"][0])]
                )
                # Track flow types
                if dat_name:
                    flow_type, _ = dat_name.rsplit("_", 1)
                    if flow_type != last_flow_type:
                        # Flow type has switched. Record the end of this flow type
                        if last_flow_type in data["flowTypes"]:
                            data["flowTypes"][last_flow_type]["end"] = flow_count - 1
                        # Create a new record for this flow type
                        data["flowTypes"][flow_type] = {
                            "start": flow_count,
                            "end": None,
                        }
                        last_flow_type = flow_type
                flow_count += 1
        # Add an endpoint for the acq flows
        data["flowTypes"][last_flow_type]["end"] = flow_count
        return data

    # typedef enum {
    # 	VAL_THERMISTOR_MANIFOLD = 0,				// for Valkyrie
    # 	VAL_THERMISTOR_HEATER,			// reported as t[0]
    # 	VAL_THERMISTOR_RESTRICTOR,		// reported as t[1]
    # 	VAL_THERMISTOR_TEC,				// reported as t[2]
    # 	VAL_THERMISTOR_AMBIENT,			// reported as t[3]
    # 	VAL_THERMISTOR_MAX_VAL
    # } THERMISTOR_VALUES_VALKYRIE;

    # Valk Parsing
    def parse_flow_data_valk(fp):
        # Flot friendly format
        data = {
            "flowTypes": {},
            "pressure": {
                "manifoldPressure": {"data": [], "label": "Manifold Pressure"},
                "regulatorPressure": {"data": [], "label": "Regulator Pressure"},
            },
            "temperature": {
                "manifoldHeaterTemperature": {
                    "data": [],
                    "label": "Manifold Heater Temperature",
                },
                "wasteTemperature": {"data": [], "label": "Waste Temperature"},
                "tecTemperature": {"data": [], "label": "TEC Temperature"},
                "ambientTemperature": {"data": [], "label": "Ambient Temperature"},
                "chipTemperature": {"data": [], "label": "Chip Temperature"},
            },
        }
        reached_target_section = False
        flow_count = 0
        last_flow_type = None
        for line in fp:
            if line.startswith("ExperimentInfoLog:"):
                reached_target_section = True
            elif line.startswith("ExperimentErrorLog:"):
                break
            elif reached_target_section:
                if len(line) <= 1:
                    continue
                if line.strip().startswith("rse"):
                    continue
                if line.strip().startswith("flow"):
                    continue
                # Now we have a line we want
                dat_name, dat_meta = parse_experiment_info_log_line(line)
                # Now we need to coerce some values
                data["pressure"]["manifoldPressure"]["data"].append(
                    [flow_count, float(dat_meta["Pressure"][0])]
                )
                data["pressure"]["regulatorPressure"]["data"].append(
                    [flow_count, float(dat_meta["Pressure"][1])]
                )

                data["temperature"]["manifoldHeaterTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][0])]
                )
                data["temperature"]["wasteTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][1])]
                )
                data["temperature"]["tecTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][2])]
                )
                data["temperature"]["ambientTemperature"]["data"].append(
                    [flow_count, float(dat_meta["Temp"][3])]
                )
                # Chip temp
                data["temperature"]["chipTemperature"]["data"].append(
                    [flow_count, float(dat_meta["chipTemp"][0])]
                )

                # Track flow types
                if dat_name:
                    flow_type, _ = dat_name.rsplit("_", 1)
                    if flow_type != last_flow_type:
                        # Flow type has switched. Record the end of this flow type
                        if last_flow_type in data["flowTypes"]:
                            data["flowTypes"][last_flow_type]["end"] = flow_count - 1
                        # Create a new record for this flow type
                        data["flowTypes"][flow_type] = {
                            "start": flow_count,
                            "end": None,
                        }
                        last_flow_type = flow_type
                flow_count += 1
        # Add an endpoint for the acq flows
        data["flowTypes"][last_flow_type]["end"] = flow_count
        return data

    with open(exp_log_file_path) as exp_log_file:
        flow_data = {}
        if archive_type == "PGM_Run":
            pgm_version = explog.get("PGM HW", "").strip()
            if pgm_version == "1.1":
                flow_data = parse_flow_data_pgm(exp_log_file, True)
            elif pgm_version == "1.0":
                flow_data = parse_flow_data_pgm(exp_log_file, False)
            else:
                raise KeyError("Unknown PGM Version:%s" % pgm_version)
        elif archive_type == "Proton":
            flow_data = parse_flow_data_proton(exp_log_file)
        elif archive_type == "S5":
            flow_data = parse_flow_data_s5(exp_log_file)
        elif archive_type == "Valkyrie":
            flow_data = parse_flow_data_valk(exp_log_file)
        else:
            raise KeyError("Unknown device type:%s" % archive_type)

    level = INFO
    start_at_flow = 0
    if "flowTypes" in flow_data:
        start_at_flow = flow_data["flowTypes"]["acq"]["start"]

    # Check pressure and temp bounds
    pressure_message = None
    try:
        validate_data_within_limits(
            flow_data["pressure"], PRESSURE_LIMITS[archive_type], start_at_flow
        )
    except OutOfRangeError as e:
        pressure_message = e.message
        level = e.level if e.level > level else level

    temperature_message = None
    try:
        validate_data_within_limits(
            flow_data["temperature"], TEMP_LIMITS[archive_type], start_at_flow
        )
    except OutOfRangeError as e:
        temperature_message = e.message
        level = e.level if e.level > level else level

    # Convert the flow data dicts into lists
    flow_data["pressure"] = flow_data["pressure"].values()
    flow_data["temperature"] = flow_data["temperature"].values()

    return pressure_message, temperature_message, level, flow_data


def execute(archive_path, output_path, archive_type):
    (
        pressure_message,
        temperature_message,
        message_level,
        flow_data,
    ) = get_pressure_and_temp(archive_path, archive_type)

    write_results_from_template(
        {
            "pressure_message": pressure_message,
            "temperature_message": temperature_message,
            "raw_data": json.dumps(flow_data),
        },
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    message = ["See results for details."]
    if temperature_message:
        message = [temperature_message] + message
    if pressure_message:
        message = [pressure_message] + message

    # Write out status
    if message_level == INFO:
        return print_info(" | ".join(message))
    elif message_level == WARN:
        return print_warning(" | ".join(message))
    else:
        return print_alert(" | ".join(message))


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
