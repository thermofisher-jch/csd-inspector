#!/usr/bin/env python
import os
import csv
import fnmatch
import copy
from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    print_alert,
    print_ok,
    write_results_from_template,
)

PASS = "Passed"
FAIL = "Failed"
NA = "Not Calculated"


def get_qc_dict(rows):
    #
    def init_d():
        return {"header": "", "type": "", "keys": [], "metrics": []}

    q = init_d()
    header = ""
    blank_cnt = 0
    start_metrics = False
    for row in rows:
        if len(row) == 0:
            blank_cnt += 1

            # metrics section ends when a blank line
            if start_metrics:
                yield q
                q = init_d()
                start_metrics = False
        else:
            blank_cnt = 0

        if blank_cnt > 1:
            # skip when multiple blank lines
            continue

        """
        # either it is header or type
        Sample QC Evaluation Metrics

        DNA

        Metric Name,Value,Reference Range,QC Status
        
        """
        if len(row) == 1:
            k = row.pop()
            if "QC" in k and k.endswith("Metrics"):
                header = k
                q = init_d()
                q["header"] = header
            else:
                q = init_d()
                q["header"] = header
                q["type"] = k

        """
        # when multiple element per lines, likely starting QC Metric Sections
        
        Metric Name,Value,Reference Range,QC Status
        Key Signal,55,Not Set,Not Calculated
        Percent Loading,90.6,Not Set,Not Calculated
        Raw Read Accuracy,98.6,Not Set,Not Calculated

        """
        if len(row) > 1:
            name = row[0]
            if name.startswith("Metric Name"):
                q["keys"] = row
                start_metrics = True
                continue

            if start_metrics:
                m = {}
                keys = q["keys"]
                for i, k in enumerate(keys):
                    m[k] = row[i]
                q["metrics"].append(m)


def find_sample_name(rows):
    for row in rows:
        if len(row) < 2:
            continue
        if "sample name" in row[0].lower():
            return row[1]
    return "Unknown Sample"


def get_other_details(rows):
    other_headers = [
        "Software Version Details",
        "Sample Details",
        "Library Details",
        "Run Details",
        "Assay Details",
        "Reagent Information",
        "Consumable Information",
        "Analysis",
        "Instrument Summary",
        "Evaluation Metrics",
    ]
    other_runDetails = {}
    tempHeader = None
    for row in rows:
        if len(row):
            if any(header in row[0] for header in other_headers):
                tempHeader = row[0]
                if "Evaluation Metrics" not in tempHeader:
                    other_runDetails[tempHeader] = []
                continue
            if (
                "Evaluation Metrics" not in tempHeader
                and tempHeader in other_runDetails
            ):
                other_runDetails[tempHeader].append(row)

    return other_runDetails


def runLevelQcData(qc_detail):
    section = qc_detail.get("header")  # section header, i.e. Run QC/ Control QC Metrics
    type_name = qc_detail.get("type")
    run_level_failedQc = 0
    run_level_data = {
        "qc_status": NA,
        "keys": [],
        "metrics": {},
    }

    if section not in run_level_data["metrics"]:
        run_level_data["metrics"][section] = []
    run_level_data["keys"] = qc_detail.get("keys")
    for m in qc_detail.get("metrics", []):
        run_level_data["qc_status"] = m["QC Status"]
        # any fail -> fail
        if m["QC Status"] == FAIL:
            run_level_failedQc += 1

        if type_name:
            m["Metric Name"] = "%s %s" % (type_name, m["Metric Name"])
        run_level_data["metrics"][section].append(m)
    return run_level_failedQc, run_level_data


def populate_samples(sample_name, rows):
    sample_data = {
        "sample_name": sample_name,
        "qc_status": NA,
        "keys": [],
        "metrics": {},
    }

    failed_samples = {
        "sample_name": sample_name,
        "qc_status": NA,
        "keys": [],
        "metrics": {},
    }

    runQc_data = {}
    run_level_failedQcs = {}
    controlQc_data = {}
    for qc_detail in get_qc_dict(rows):
        section = qc_detail.get("header")  # section header, i.e. Run QC Metrics
        type_name = qc_detail.get("type")

        if "Run QC" in section and not bool(runQc_data):
            run_level_failedQc, runQc_data = runLevelQcData(qc_detail)
            if run_level_failedQc:
                run_level_failedQcs["failedRunQc"] = run_level_failedQc
            continue

        if "Control QC" in section and not bool(controlQc_data):
            run_level_failedQc, controlQc_data = runLevelQcData(qc_detail)
            if run_level_failedQc:
                run_level_failedQcs["failedControlQc"] = run_level_failedQc
            continue

        # assuming all qc_details have the same keys, so last one gets used.
        sample_data["keys"] = qc_detail.get("keys")
        failed_samples["keys"] = qc_detail.get("keys")

        if section not in sample_data["metrics"]:
            sample_data["metrics"][section] = []

        for m in qc_detail.get("metrics", []):
            # any fail -> fail
            if m["QC Status"] == FAIL:
                sample_data["qc_status"] = FAIL
                failed_samples["qc_status"] = FAIL

            # set pass only when NA
            if m["QC Status"] == PASS and sample_data["qc_status"] == NA:
                sample_data["qc_status"] = PASS

            if type_name:
                m["Metric Name"] = "%s %s" % (type_name, m["Metric Name"])

            sample_data["metrics"][section].append(m)
            if m["QC Status"] == FAIL:
                if section not in failed_samples["metrics"]:
                    failed_samples["metrics"][section] = []
                failed_samples["metrics"][section].append(m)

    return sample_data, failed_samples, runQc_data, controlQc_data, run_level_failedQcs


def transform_data_for_display(sample_data):
    """
    qc_data:
        list_sections:
            section_name -> h3
            rows -> values
    """
    sections = sample_data["metrics"].keys()
    metrics_names = sample_data["keys"]
    sections_data = []
    for sect in sections:
        metrics = sample_data["metrics"][sect]
        metrics_values = []
        for m in metrics:
            metrics_values.append([m[k] for k in metrics_names])
        sections_data.append(metrics_values)

    return metrics_names, zip(sections, sections_data)


def execute(archive_path, output_path, archive_type):
    results = {"num_failed_samples": 0, "samples": []}
    info_per_sample = []
    failed_samples = []
    run_level_runQcdata = []
    run_level_controlQcdata = []
    infoRowsForOtherDetails = None
    for root, dirnames, filenames in os.walk(os.path.join(archive_path, "CSA")):
        for filename in fnmatch.filter(filenames, "Info.csv"):
            with open(os.path.join(root, filename), "rb") as fp:
                info_rows = list(csv.reader(fp, delimiter=","))
                sample_name = find_sample_name(info_rows)

                infoRowsForOtherDetails = copy.deepcopy(info_rows)
                (
                    sample_data,
                    failed_data,
                    runQc_data,
                    controlQc_data,
                    run_level_failedQcs,
                ) = populate_samples(sample_name, info_rows)
                metrics_names, qc_data = transform_data_for_display(sample_data)
                _, failed_qc_data = transform_data_for_display(failed_data)
                _, runQc_data = transform_data_for_display(runQc_data)
                _, controlQc_data = transform_data_for_display(controlQc_data)

                info_per_sample.append([sample_name, info_rows, metrics_names, qc_data])
                run_level_runQcdata.append([metrics_names, runQc_data])
                run_level_controlQcdata.append([metrics_names, controlQc_data])
                if failed_data["qc_status"] == FAIL:
                    failed_samples.append(
                        [sample_name, None, metrics_names, failed_qc_data]
                    )

                # results.json
                if sample_data["qc_status"] == FAIL:
                    results["num_failed_samples"] += 1
                results["samples"].append(sample_data)

    info_per_sample.sort(key=lambda x: x[0])
    write_results_from_template(
        {
            "info_per_sample": info_per_sample,
            "failed_samples": failed_samples,
            "run_level_data": [[run_level_runQcdata[0]], [run_level_controlQcdata[0]]],
            "other_runDetails": get_other_details(infoRowsForOtherDetails),
        },
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )
    alertMessages = []
    if results["num_failed_samples"] == 1:
        alertMessages.append(
            "%d sample has failed QC check" % results["num_failed_samples"]
        )
    elif results["num_failed_samples"] > 1:
        alertMessages.append(
            "%d samples have failed QC check" % results["num_failed_samples"]
        )

    if run_level_failedQcs.get("failedRunQc", ""):
        if run_level_failedQcs["failedRunQc"] == 1:
            alertMessages.append(
                "%d Run QC has failed" % run_level_failedQcs["failedRunQc"]
            )
        else:
            alertMessages.append(
                "%d Run QCs failed" % run_level_failedQcs["failedRunQc"]
            )
    if run_level_failedQcs.get("failedControlQc", ""):
        if run_level_failedQcs.get("failedControlQc") == 1:
            alertMessages.append(
                "%d Control QC has failed" % run_level_failedQcs["failedControlQc"]
            )
        else:
            alertMessages.append(
                "%d Control QCs have failed" % run_level_failedQcs["failedControlQc"]
            )

    if alertMessages:
        return print_alert(" | ".join(alertMessages))
    else:
        num_pass = 0
        for sample in results["samples"]:
            if sample["qc_status"] == PASS:
                num_pass += 1

        if num_pass > 1:
            return print_ok("%d samples have passed QC check." % num_pass)

    return print_info("See results for details.")
