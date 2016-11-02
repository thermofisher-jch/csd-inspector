#!/usr/bin/env python

import sys
import os
import json
import collections

from lemontest.diagnostics.common.inspector_utils import print_info, handle_exception

archive_path, output_path, device_type = sys.argv[1:4]
exp_log_file_path = os.path.join(archive_path, "explog_final.txt")
template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "results.html")
results_path = os.path.join(output_path, "results.html")


# Shared parser. Used by proton and s5 to parse some strange log lines
def parse_experiment_info_log_line(line):
    """ ExperimentInfoLog: is in a very odd format with line like
        acq_0272.dat: Pressure=7.91 7.95 Temp=39.99 31.19 30.01 26.64 dac_start_sig=1724
        """
    dat_meta = collections.OrderedDict()
    dat_name, dat_meta_string = line.strip().split(":", 1)
    for token in dat_meta_string.strip().split(" "):
        if "=" in token:  # After tokenizing by spaces, some token are values, and some are keys and values
            key, value = token.split("=")
            dat_meta[key] = [value]
        else:  # If there is no = this token is a value
            dat_meta[dat_meta.keys()[-1]].append(token)
    return dat_name, dat_meta


# PGM Parsing
def parse_flow_data_pgm(fp):
    # Flot friendly format
    data = {
        "pressure": {
            "pressure": {"data": [], "label": "Pressure"},
        },
        "temperature": {
            "internalTemperature": {"data": [], "label": "Internal Temperature"},
            "restrictorTemperature": {"data": [], "label": "Restrictor Temperature"},
            "chipHeatsinkTemperature": {"data": [], "label": "Chip Heatsink Temperature"},
            "chipTemperature": {"data": [], "label": "Chip Temperature"},
        }
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
            data["pressure"]["pressure"]["data"].append([flow_count, float(dat_meta[1])])
            data["temperature"]["internalTemperature"]["data"].append([flow_count, float(dat_meta[2])])
            data["temperature"]["restrictorTemperature"]["data"].append([flow_count, float(dat_meta[3])])
            data["temperature"]["chipHeatsinkTemperature"]["data"].append([flow_count, float(dat_meta[4])])
            data["temperature"]["chipTemperature"]["data"].append([flow_count, float(dat_meta[5])])
            flow_count += 1
    return data


# Proton Parsing
def parse_flow_data_proton(fp):
    # Flot friendly format
    data = {
        "pressure": {
            "manifoldPressure": {"data": [], "label": "Manifold Pressure"},
            "regulatorPressure": {"data": [], "label": "Regulator Pressure"},
        },
        "temperature": {
            "chipBayTemperature": {"data": [], "label": "Chip Bay Temperature"},
            "ambientTemperature": {"data": [], "label": "Ambient Temperature"},
            "underChipTemperature": {"data": [], "label": "Under Chip Temperature"}
        }
    }
    reached_target_section = False
    flow_count = 0
    for line in fp:
        if line.startswith("ExperimentInfoLog:"):
            reached_target_section = True
        elif line.startswith("ExperimentErrorLog:"):
            break
        elif reached_target_section and len(line) > 1:
            # Now we have a line we want
            dat_name, dat_meta = parse_experiment_info_log_line(line)
            # Now we need to coerce some values
            data["pressure"]["manifoldPressure"]["data"].append([flow_count, float(dat_meta["Pressure"][1])])
            data["pressure"]["regulatorPressure"]["data"].append([flow_count, float(dat_meta["Pressure"][0])])
            # https://stash.amer.thermo.com/projects/TS/repos/rndplugins/browse/autoCal/autoCal.R
            # 'Chip Bay','Ambient','Under Chip'
            data["temperature"]["chipBayTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][0])])
            data["temperature"]["ambientTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][1])])
            data["temperature"]["underChipTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][2])])
            flow_count += 1
    return data


# S5 Parsing
def parse_flow_data_s5(fp):
    # Flot friendly format
    data = {
        "pressure": {
            "manifoldPressure": {"data": [], "label": "Manifold Pressure"},
            "regulatorPressure": {"data": [], "label": "Regulator Pressure"},
        },
        "temperature": {
            "manifoldTemperature": {"data": [], "label": "Manifold Temperature"},
            "manifoldHeaterTemperature": {"data": [], "label": "Manifold Heater Temperature"},
            "wasteTemperature": {"data": [], "label": "Waste Temperature"},
            "tecTemperature": {"data": [], "label": "TEC Temperature"},
            "ambientTemperature": {"data": [], "label": "Ambient Temperature"}
        }
    }
    reached_target_section = False
    flow_count = 0
    for line in fp:
        if line.startswith("ExperimentInfoLog:"):
            reached_target_section = True
        elif line.startswith("ExperimentErrorLog:"):
            break
        elif reached_target_section and len(line) > 1:
            # Now we have a line we want
            dat_name, dat_meta = parse_experiment_info_log_line(line)
            # Now we need to coerce some values
            data["pressure"]["manifoldPressure"]["data"].append([flow_count, float(dat_meta["Pressure"][1])])
            data["pressure"]["regulatorPressure"]["data"].append([flow_count, float(dat_meta["Pressure"][0])])
            # https://stash.amer.thermo.com/projects/TS/repos/rndplugins/browse/autoCal/autoCal.R
            # 'manifold heater','manifold','TEC','waste','ambient'
            # I think these values are labeled wrong by the autoCal plugin. But copied for consistency.
            data["temperature"]["manifoldHeaterTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][0])])
            data["temperature"]["manifoldTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][1])])
            data["temperature"]["tecTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][2])])
            data["temperature"]["ambientTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][3])])
            data["temperature"]["wasteTemperature"]["data"].append(
                [flow_count, float(dat_meta["ManTemp"][0])]
            )
            flow_count += 1
    return data


with open(exp_log_file_path) as exp_log_file:
    flow_data = {}
    try:
        if device_type == "PGM_Run":
            flow_data = parse_flow_data_pgm(exp_log_file)
        elif device_type == "Proton":
            flow_data = parse_flow_data_proton(exp_log_file)
        elif device_type == "Raptor_S5":
            flow_data = parse_flow_data_s5(exp_log_file)
        else:
            raise KeyError("Unknown device type:%s" % device_type)
    except Exception as e:
        handle_exception(e, output_path)
        exit()

    # Convert the flow data dicts into lists
    flow_data["pressure"] = flow_data["pressure"].values()
    flow_data["temperature"] = flow_data["temperature"].values()

    # Write out results html
    with open(template_path, "r") as template_file:
        with open(results_path, "w") as results_file:
            results_file.write(template_file.read().replace("\"%raw_data%\"", json.dumps(flow_data)))

    # Write out status
    print_info("See results for details.")
