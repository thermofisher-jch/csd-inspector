#!/usr/bin/env python

import ConfigParser
import semver
import os
import shutil
import glob
import json
from reports.diagnostics.common.inspector_utils import (
    read_explog,
    check_supported,
    get_chip_type_from_exp_log,
    write_results_from_template,
    print_warning,
    print_alert,
    print_ok,
    read_ionstats_basecaller_json,
    format_reads,
)
from reports.diagnostics.common.inspector_errors import FileNotFoundError

REPORT_LEVEL_INFO = 0
REPORT_LEVEL_WARN = 1
REPORT_LEVEL_ALERT = 2

# the ranges based on chip type for which the gain value is valid
PGM_GAIN_RANGE = (0.67, 0.71)
PROTON_S5_GAIN_RANGE = (0.9, 1.2)
VALKYRIE_GAIN_RANGE = (0.75, 1.06)
VALKYRIE_GX7_GAIN_RANGE = (0.937, 1.143)

gain_ranges = {
    "314": PGM_GAIN_RANGE,
    "316": PGM_GAIN_RANGE,
    "318": PGM_GAIN_RANGE,
    "P1": PROTON_S5_GAIN_RANGE,
    "510": PROTON_S5_GAIN_RANGE,
    "520": PROTON_S5_GAIN_RANGE,
    "530": PROTON_S5_GAIN_RANGE,
    "540": PROTON_S5_GAIN_RANGE,
    "550": PROTON_S5_GAIN_RANGE,
    "PQ": (1.1, 1.4),
    "GX5": VALKYRIE_GAIN_RANGE,
    "GX7": VALKYRIE_GX7_GAIN_RANGE,
}

noise_thresholds = {
    "314": 6.0,
    "316": 8.0,
    "318": 10.0,
    "P1": 170,
    "510": 90,
    "520": 90,
    "530": 90,
    "540": 170,
    "550": 185,
    "PQ": 280,
    "GX5": 122,
    "GX7": 147,
}

electrode_ranges = {
    "314": (0.4, 1.20),
    "316": (0.4, 1.20),
    "318": (0.4, 1.20),
    "P1": (170.0, 170.0),
}

total_read_specs = {
    # name: multiplier, expected read count
    "314": (1, 400000),
    "316": (1, 2000000),
    "318": (1, 4000000),
    "P1": (166, 60000000),
    "510": (6.6, 2000000),
    "520": (13.4, 3000000),
    "530": (41, 15000000),
    "540": (166, 60000000),
    "GX5": (1, 100000000),
}


def parse_base_caller_stats(archive_path):
    path = os.path.join(
        archive_path, "CSA", "outputs", "BaseCallingActor-00", "BaseCaller.json"
    )
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path) as fp:
        stats = json.load(fp)
        return (
            stats["Filtering"]["ReadDetails"]["lib"],
            stats["Filtering"]["BaseDetails"],
        )


def copy_chipDiagnosticsReportfiles(archive_path, output_path):
    chipDiagnosticsReportfiles = [
        "pix_offset_spatial.png",
        "pix_offset_histogram.png",
        "chip_dac.png",
        "calibration.html",
        "gain_spatial.png",
        "chip_thermometer_temperature.png",
        "gain_histogram.png",
        "noise_spatial.png",
        "noise_histogram.png",
    ]
    chip_images_found = {}
    for image in chipDiagnosticsReportfiles:
        imagePath = os.path.join(archive_path, "chipDiagnostics", image)
        if os.path.exists(imagePath):
            shutil.copy(imagePath, output_path)
            chip_images_found[image] = True
        else:
            chip_images_found[image] = False
    return chip_images_found


def copy_chip_images(archive_path, output_path):
    chip_images_html_path = os.path.join(
        archive_path, "ValkyrieWorkflow/chipImages.html"
    )
    chip_images_found = copy_chipDiagnosticsReportfiles(archive_path, output_path)
    if os.path.exists(chip_images_html_path):
        shutil.copy(
            chip_images_html_path, os.path.join(output_path, "chip_images.html")
        )
        for image in glob.glob(archive_path + "/ValkyrieWorkflow/*.jpg"):
            shutil.copy(image, output_path)
        chip_images_found["chip_images.html"] = True
    else:
        chip_images_found["chip_images.html"] = False
    return chip_images_found


def get_total_reads(archive_path, archive_type):
    ionstats = read_ionstats_basecaller_json(archive_path, archive_type)
    total_reads = ionstats["full"]["num_reads"]
    return total_reads


def get_total_reads_message(chip_type, total_reads):
    try:
        reads_multiplier, min_reads = total_read_specs[chip_type]
    except KeyError:
        return None, total_reads, None
    full_chip_reads = total_reads * reads_multiplier
    if reads_multiplier == 1:
        return (
            "Total Reads {}".format(format_reads(full_chip_reads)),
            full_chip_reads,
            min_reads,
        )
    else:
        return (
            "Projected Reads {}".format(format_reads(full_chip_reads)),
            full_chip_reads,
            min_reads,
        )


def load_ini(file_path, namespace="global"):
    parse = ConfigParser.ConfigParser()
    # preserve the case
    parse.optionxform = str
    parse.read(file_path)
    return dict(parse.items(namespace))


def get_chip_status(archive_path, output_path, archive_type):
    # get the path to the log file
    data = read_explog(archive_path)
    check_supported(data)
    chip_type = get_chip_type_from_exp_log(data)
    report_level = REPORT_LEVEL_INFO

    # check to see if the we have a lookup value for the chip type
    if chip_type not in noise_thresholds:
        raise Exception("No known thresholds for chip type " + chip_type)

    if chip_type not in gain_ranges:
        raise Exception("No known range for chip type " + chip_type)

    if "Gain" not in data and "ChipGain" not in data:
        raise Exception("No chip gain recorded.")

    # find the correct key for the noise value
    noise = data.get("ChipNoise", None) or data.get("Noise", None)
    if not noise:
        raise Exception("The noise value could not be found in the log.")
    noise = round(float(noise), 2)

    # there is a known issue with 5.6 reporting the noise levels of 510 and 520 chips
    # so we lost the noise information for these sets
    invalid_noise = False
    release_version = (
        data.get("S5 Release_version")
        or data.get("Proton Release_version")
        or data.get("PGM SW Release")
    )
    if release_version:
        if release_version.count(".") < 2:
            release_version = release_version + ".0"
        if semver.match(release_version, ">=5.6.0"):
            invalid_noise = data.get("ChipVersion") in ["510", "520"]

    noise_alert = noise > noise_thresholds[chip_type]
    noise_report = (
        "Chip noise "
        + str(noise)
        + (" is too high." if noise_alert else " is low enough.")
    )
    if noise_alert and not invalid_noise:
        report_level = max(report_level, REPORT_LEVEL_ALERT)

    # detect issues with the gain
    low, high = gain_ranges[chip_type]
    gain = round(float(data["Gain"] if "Gain" in data else data["ChipGain"]), 2)
    if gain > high:
        gain_report = "Chip gain {} is high.".format(gain)
    elif gain < low:
        gain_report = "Chip gain {} is low.".format(gain)
    else:
        gain_report = "Chip gain {} is within range.".format(gain)

    # detect reference electrode record indicating pgm and look for issues
    electrode_report = ""
    electrode_gain = None
    if "Ref Electrode" in data and chip_type in electrode_ranges:
        electrode_low, electrode_high = electrode_ranges[chip_type]
        electrode_gain = round(float(data["Ref Electrode"].split(" ")[0]), 2)
        if electrode_gain > electrode_high:
            electrode_report = "Reference Electrode {} is high.".format(electrode_gain)
        elif electrode_gain < electrode_low:
            electrode_report = "Reference Electrode {} is low.".format(electrode_gain)
        else:
            electrode_report = "Reference Electrode {} is within range.".format(
                electrode_gain
            )

    # get the isp loading
    bead_loading = None
    isp_report = None
    if chip_type != "314":
        stats_path = None
        for file_name in [
            "sigproc_results/analysis.bfmask.stats",
            "sigproc_results/bfmask.stats",
            "CSA/outputs/SigProcActor-00/analysis.bfmask.stats",
        ]:
            path = os.path.join(archive_path, file_name)
            if os.path.exists(path):
                stats_path = path
                break

        if stats_path:
            data = load_ini(stats_path)
            bead_loading = float(data["Bead Wells"]) / (
                float(data["Total Wells"]) - float(data["Excluded Wells"])
            )
            isp_report = "{:.1%} of wells found ISPs".format(bead_loading)
        else:
            isp_report = "Required stats files not included"

    # total reads
    total_reads = None
    full_candidate = None
    total_reads_message = None
    try:
        total_reads = get_total_reads(archive_path, archive_type)
        (
            total_reads_message,
            full_chip_reads,
            full_chip_reads_spec,
        ) = get_total_reads_message(chip_type, total_reads)
    except:
        total_reads_message = "Total Reads not known"

    # final reads
    final_reads_message = None
    if archive_type == "Valkyrie":
        try:
            base_caller_read_stats, base_caller_base_stats = parse_base_caller_stats(
                archive_path
            )
            final_reads = base_caller_read_stats["valid"]
            final_reads_message = "Final Reads {}".format(format_reads(final_reads))
        except FileNotFoundError:
            final_reads_message = "Final Reads not known"

    # generate message
    message = "Loading {} | Gain {}".format(
        "{:.1%}".format(bead_loading) if bead_loading else "Unknown", gain or "Unknown"
    )
    if not invalid_noise:
        message += " | Noise {}".format(noise or "Unknown")

    if electrode_gain:
        message += " | Reference Electrode {}".format(electrode_gain)

    if final_reads_message:
        message += " | " + final_reads_message
    elif total_reads_message:
        message += " | " + total_reads_message

    chip_images_found = copy_chip_images(archive_path, output_path)
    context = {
        "bead_loading": bead_loading,
        "total_reads": total_reads,
        "chip_images_found": chip_images_found["chip_images.html"],
        "calibration_found": chip_images_found["calibration.html"],
        "pix_offset_spatial_found": chip_images_found["pix_offset_spatial.png"],
        "pix_offset_histogram_found": chip_images_found["pix_offset_histogram.png"],
        "noise_report": noise_report,
        "gain_report": gain_report,
        "electrode_report": electrode_report,
        "isp_report": isp_report,
        "invalid_noise": invalid_noise,
        "total_reads_message": total_reads_message,
    }

    return message, report_level, context


def execute(archive_path, output_path, archive_type):
    message, report_level, context = get_chip_status(
        archive_path, output_path, archive_type
    )

    write_results_from_template(
        context, output_path, os.path.dirname(os.path.realpath(__file__))
    )

    # details generation here
    if report_level == REPORT_LEVEL_ALERT:
        return print_alert(message)
    elif report_level == REPORT_LEVEL_WARN:
        return print_warning(message)
    else:
        return print_ok(message)
