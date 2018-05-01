#!/usr/bin/env python

import collections
import json
import os
import sys

from django.template import Context, Template

from IonInspector.reports.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        exp_log_file_path = get_explog_path(archive_path)
        if os.path.basename(exp_log_file_path) != EXPLOG_FINAL:
            return print_failed("When explog_final.txt is not found, the explog.txt is used and has limited run information so some tests will fail.")

        explog = read_explog(archive_path)
        pressure_message = ''
        temperature_message = ''
        message_level = 'info'

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
            return dat_name.strip(), dat_meta

        # PGM Parsing
        def parse_flow_data_pgm(fp, new_pgm_format):

            # get the message for the pressure
            if "PGMPressure" not in explog:
                raise Exception("PGMPressure missing from explog_final.txt")
            pressure = float(explog["PGMPressure"].split(" - ")[1])
            low, high = (9.5, 11)

            if pressure < low:
                message_level = 'alert'
                pressure_message = "PGM pressure {:.2f} is too low.".format(pressure)
            elif pressure > high:
                message_level = 'alert'
                pressure_message = "PGM pressure {:.2f} is high.".format(pressure)
            else:
                message_level = 'info'
                pressure_message = "PGM pressure {:.2f} is just right.".format(pressure)

            # get the message for the temperature
            if "PGMTemperature" not in explog:
                raise Exception("PGMTemperature missing from explog_final.txt")
            temperature = float(explog["PGMTemperature"].split(" - ")[1])
            if temperature < 26:
                message_level = 'alert'
                temperature_message = u"PGM temperature {:.2f} C is too cold.".format(temperature)
            elif temperature > 34:
                message_level = 'alert'
                temperature_message = u"PGM temperature {:.2f} C is too warm.".format(temperature)
            else:
                if message_level != 'alert':
                    message_level = 'info'
                temperature_message = u"PGM temperature {:.2f} C is just right.".format(temperature)

            # Flot friendly format
            data = {
                "pressure": {
                    "pressure": {"data": [], "label": "Pressure"},
                },
                "temperature": {
                    "internalTemperature": {"data": [], "label": "Internal Temperature"},
                    "chipTemperature": {"data": [], "label": "Chip Temperature"},
                }
            }
            if new_pgm_format:  # PGM 1.1
                data["temperature"]["restrictorTemperature"] = {"data": [], "label": "Restrictor Temperature"}
                data["temperature"]["chipHeatsinkTemperature"] = {"data": [], "label": "Chip Heatsink Temperature"}

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
                        data["pressure"]["pressure"]["data"].append([flow_count, float(dat_meta[1])])
                        data["temperature"]["internalTemperature"]["data"].append([flow_count, float(dat_meta[2])])
                        data["temperature"]["restrictorTemperature"]["data"].append([flow_count, float(dat_meta[3])])
                        data["temperature"]["chipHeatsinkTemperature"]["data"].append([flow_count, float(dat_meta[4])])
                        data["temperature"]["chipTemperature"]["data"].append([flow_count, float(dat_meta[5])])
                    else:  # PGM 1.0
                        data["pressure"]["pressure"]["data"].append([flow_count, float(dat_meta[1])])
                        data["temperature"]["internalTemperature"]["data"].append([flow_count, float(dat_meta[2])])
                        data["temperature"]["chipTemperature"]["data"].append([flow_count, float(dat_meta[3])])
                    flow_count += 1
            return data, message_level, pressure_message, temperature_message

        # Proton Parsing
        def parse_flow_data_proton(fp):
            # get the pressure message
            if "PGMPressure" not in explog and "ProtonPressure" not in explog:
                raise Exception("PGMPressure missing from explog_final.txt")
            pressure = explog.get("PGMPressure", "") or explog["ProtonPressure"]
            pressure = float(pressure.split(" ")[1])
            low, high = (10.2, 10.8)
            very_low, very_high = (10.0, 11.0)

            # Very high/low
            if pressure < very_low:
                message_level = 'alert'
                pressure_message = "Proton pressure {:.2f} is very low.".format(pressure)
            elif pressure > very_high:
                message_level = 'alert'
                pressure_message = "Proton pressure {:.2f} is very high.".format(pressure)
            # High/low
            elif pressure < low:
                message_level = 'warn'
                pressure_message = "Proton pressure {:.2f} is low.".format(pressure)
            elif pressure > high:
                message_level = 'warn'
                pressure_message = "Proton pressure {:.2f} is high.".format(pressure)
            else:
                message_level = 'info'
                pressure_message = "Proton pressure {:.2f} is just right.".format(pressure)

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
                    "ambientWasteTemperature": {"data": [], "label": "Ambient Waste Temperature"},

                    "chipTemperature": {"data": [], "label": "Chip Temperature"}
                }
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
                    data["pressure"]["manifoldPressure"]["data"].append([flow_count, float(dat_meta["Pressure"][1])])
                    data["pressure"]["regulatorPressure"]["data"].append([flow_count, float(dat_meta["Pressure"][0])])
                    # https://stash.amer.thermo.com/projects/TS/repos/rndplugins/browse/autoCal/autoCal.R
                    # 'Chip Bay','Ambient','Under Chip'
                    data["temperature"]["chipBayTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][0])])
                    data["temperature"]["ambientTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][1])])
                    data["temperature"]["ambientWasteTemperature"]["data"].append(
                        [flow_count, float(dat_meta["Temp"][3])])
                    # Chip temp
                    data["temperature"]["chipTemperature"]["data"].append([flow_count, float(dat_meta["chipTemp"][0])])
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
                                "end": None
                            }
                            last_flow_type = flow_type
                    flow_count += 1
            # Add an endpoint for the acq flows
            data["flowTypes"][last_flow_type]["end"] = flow_count

            # get the message for the temperature
            temperature_message = 'Temperature'

            min_temp = min(
                min([i for _, i in data["temperature"]["chipBayTemperature"]["data"]]),
                min([i for _, i in data["temperature"]["ambientTemperature"]["data"]]),
                min([i for _, i in data["temperature"]["ambientWasteTemperature"]["data"]])
            )

            max_temp = max(
                max([i for _, i in data["temperature"]["chipBayTemperature"]["data"]]),
                max([i for _, i in data["temperature"]["ambientTemperature"]["data"]]),
                max([i for _, i in data["temperature"]["ambientWasteTemperature"]["data"]])
            )

            if min_temp < 20:
                message_level = 'alert'
                temperature_message = u"Proton temperature {:.2f} C is too cold.".format(min_temp)
            elif max_temp > 35:
                message_level = 'alert'
                temperature_message = u"Proton temperature {:.2f} C is too warm.".format(max_temp)

            return data, message_level, pressure_message, temperature_message

        # S5 Parsing
        def parse_flow_data_s5(fp):
            # get the pressure message
            if "PGMPressure" not in explog and "ProtonPressure" not in explog:
                raise Exception("PGMPressure missing from explog_final.txt")
            pressure = explog.get("PGMPressure", "") or explog["ProtonPressure"]
            pressure = float(pressure.split(" ")[1])
            low, high = (7.2, 8.8)

            if pressure < low:
                message_level = 'alert'
                pressure_message = "S5 pressure {:.2f} is too low.".format(pressure)
            elif pressure > high:
                message_level = 'alert'
                pressure_message = "S5 pressure {:.2f} is high.".format(pressure)
            else:
                message_level = 'info'
                pressure_message = "S5 pressure {:.2f} is just right.".format(pressure)

            # Flot friendly format
            data = {
                "flowTypes": {},
                "pressure": {
                    "manifoldPressure": {"data": [], "label": "Manifold Pressure"},
                    "regulatorPressure": {"data": [], "label": "Regulator Pressure"},
                },
                "temperature": {
                    "manifoldHeaterTemperature": {"data": [], "label": "Manifold Heater Temperature"},
                    "wasteTemperature": {"data": [], "label": "Waste Temperature"},
                    "tecTemperature": {"data": [], "label": "TEC Temperature"},
                    "ambientTemperature": {"data": [], "label": "Ambient Temperature"},

                    "chipTemperature": {"data": [], "label": "Chip Temperature"},
                    "manifoldTemperature": {"data": [], "label": "Manifold Temperature"},
                }
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
                    data["pressure"]["manifoldPressure"]["data"].append([flow_count, float(dat_meta["Pressure"][1])])
                    data["pressure"]["regulatorPressure"]["data"].append([flow_count, float(dat_meta["Pressure"][0])])

                    data["temperature"]["manifoldHeaterTemperature"]["data"].append(
                        [flow_count, float(dat_meta["Temp"][0])])
                    data["temperature"]["wasteTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][1])])
                    data["temperature"]["tecTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][2])])
                    data["temperature"]["ambientTemperature"]["data"].append([flow_count, float(dat_meta["Temp"][3])])
                    # Chip temp
                    data["temperature"]["chipTemperature"]["data"].append([flow_count, float(dat_meta["chipTemp"][0])])
                    # Man temp
                    data["temperature"]["manifoldTemperature"]["data"].append(
                        [flow_count, float(dat_meta["ManTemp"][0])])
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
                                "end": None
                            }
                            last_flow_type = flow_type
                    flow_count += 1
            # Add an endpoint for the acq flows
            data["flowTypes"][last_flow_type]["end"] = flow_count

            # get the message for the temperature
            temperature_message = 'Temperature'

            min_temp = min(
                min([i for _, i in data["temperature"]["ambientTemperature"]["data"]]),
                min([i for _, i in data["temperature"]["wasteTemperature"]["data"]]),
                min([i for _, i in data["temperature"]["manifoldTemperature"]["data"]])
            )

            max_temp = max(
                max([i for _, i in data["temperature"]["ambientTemperature"]["data"]]),
                max([i for _, i in data["temperature"]["wasteTemperature"]["data"]]),
                max([i for _, i in data["temperature"]["manifoldTemperature"]["data"]])
            )

            if min_temp < 20:
                message_level = 'alert'
                temperature_message = u"S5 temperature {:.2f} C is too cold.".format(min_temp)
            elif max_temp > 35:
                message_level = 'alert'
                temperature_message = u"S5 temperature {:.2f} C is too warm.".format(max_temp)

            return data, message_level, pressure_message, temperature_message

        with open(exp_log_file_path) as exp_log_file:
            flow_data = {}
            if archive_type == "PGM_Run":
                pgm_version = explog.get("PGM HW", "").strip()
                if pgm_version == "1.1":
                    flow_data, message_level, pressure_message, temperature_message = parse_flow_data_pgm(exp_log_file,
                                                                                                          True)
                elif pgm_version == "1.0":
                    flow_data, message_level, pressure_message, temperature_message = parse_flow_data_pgm(exp_log_file,
                                                                                                          False)
                else:
                    raise KeyError("Unknown PGM Version:%s" % pgm_version)
            elif archive_type == "Proton":
                flow_data, message_level, pressure_message, temperature_message = parse_flow_data_proton(exp_log_file)
            elif archive_type == "S5":
                flow_data, message_level, pressure_message, temperature_message = parse_flow_data_s5(exp_log_file)
            else:
                raise KeyError("Unknown device type:%s" % archive_type)

        # Convert the flow data dicts into lists
        flow_data["pressure"] = flow_data["pressure"].values()
        flow_data["temperature"] = flow_data["temperature"].values()

        write_results_from_template({
            "pressure_message": pressure_message,
            "temperature_message": temperature_message,
            "raw_data": json.dumps(flow_data),
        }, output_path, os.path.dirname(os.path.realpath(__file__)))

        # Write out status
        if message_level == 'info':
            return print_info("See results for details.")
        elif message_level == 'warn':
            return print_warning("See results for details.")
        else:
            return print_alert("See results for details.")
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
