#!/usr/bin/env python

import os
import json
import sys

from django.utils.safestring import SafeString
import pandas as pd

from reports.diagnostics.Purification_Run_Log.pure_utility import (
    find_purification_files,
)
from reports.diagnostics.common.inspector_errors import (
    FileNotFoundError,
    FilesNotFoundError,
)
from reports.diagnostics.common.inspector_utils import (
    print_alert,
    print_info,
    write_results_from_template,
)


class ColumnMeta:
    def __init__(self, header, legend, parser):
        self.header = header
        self.legend = legend
        self.parser = parser


def parse_norm_temp(temp_str):
    return float(temp_str) / 10.0


# TIMESTAMP_COLUMN_META = ColumnMeta(
#     header = "time",
#     legend = "Time since experiment start (seconds)",
#     parser = parse
# )

# Fan tachometer readings
TARGET_FAN_FIELDS = [
    ColumnMeta("SystemFanTach", "System Fan", float),
    ColumnMeta("CoolingFan1", "Cooling Fan 1", float),
    ColumnMeta("CoolingFan2", "Cooling Fan 2", float),
    ColumnMeta("CoolingPumpTach", "Cooling Pump", float),
]

# Temperature-based columns
TARGET_TEMP_FIELDS = [
    ColumnMeta("Ambient1", "Ambient 1", float),
    ColumnMeta("Ambient1.1", "Ambient 2", float),
    ColumnMeta("DeckTemp", "Deck", float),
    ColumnMeta("LiquidCooling", "Liquid Cooling", float),
    ColumnMeta("24WellPlate1", "24-Well Plate 1", float),
    ColumnMeta("24WellPlate1HeatSink", "24-Well Plate 1 Heat-Sink", float),
    ColumnMeta("24WellPlate2", "24-Well Plate 2", float),
    ColumnMeta("24WellPlate2HeatSink", "24-Well Plate 2 Heat-Sink", float),
    ColumnMeta("96WellPlate1", "96-Well Plate 1", float),
    ColumnMeta("96WellPlate1HeatSink", "96-Well Plate 1 Heat-Sink", float),
    ColumnMeta("96WellPlate2", "96-Well Plate 2", float),
    ColumnMeta("96WellPlate2HeatSink", "96-Well Plate 2 Heat-Sink", float),
    ColumnMeta("QuantConsumable", "Quant Consumable", float),
    ColumnMeta("QuantConsumableHeatSink", "Quant Consumable Heat-Sink", float),
    ColumnMeta("OutputPlate", "Output Plate", float),
    ColumnMeta("outputPlateHeatsink", "Output Plate Heat-Sink", float),
    ColumnMeta("ArchivePlate", "Archive Plate", float),
    ColumnMeta("ArchivePlateHeatSink", "Archive Plate Heat-Sink", float),
]

TARGET_MISC_FIELDS = [
    ColumnMeta("CurrentLight", "Light (lux)", float),
    ColumnMeta("CurrentQuant", "Quant (q)", float),
    ColumnMeta("CurrentStepper", "Steps (step)", float),
]

GAP_TOLERANCE = 45
NO_DATE = pd.Timestamp(0)


def gen_left_only_split(threshold):
    def left_short_split(x):
        left_delta = x["time"] - x["interval"].left
        if left_delta.seconds > threshold:
            return x["interval"].left + (left_delta / 2)
        else:
            return NO_DATE

    return left_short_split


def gen_right_only_split(threshold):
    def right_short_split(x):
        right_delta = x["interval"].right - x["time"]
        if right_delta.seconds > threshold:
            return x["time"] + (right_delta / 2)
        else:
            return NO_DATE

    return right_short_split


def short_split(x):
    left_delta = x["time"] - x["interval"].left
    right_delta = x["interval"].right - x["time"]
    if left_delta > right_delta:
        return x["interval"].left + (left_delta / 2)
    else:
        return x["time"] + (right_delta / 2)


def load_plan_log_csv(run_log_csv_path):
    """
    The csv may begin before the target run, but it will not run beyond the its end.
    Partial data collection from before the actual run manifests as extra data followed
    by additional header rows.  To filter it out, we ask Pandas to re-index the CSV using
    the time column and the original line-number index column.   This lets use query the
    index for all 'time' column rows with a value that matches 'time'.  The largest such
    match bears the line number of the last row before real data began,
    #
    Once we have found the last line we want to remove, we return to the original loaded
    CSV file-sourced DataFrame and remove the first N rows, where N was found as described
    above.  The transformed DataFrame returned cn now be safely re-indexed by only the
    time column, since it will no longer have duplicate copies of the string 'time', and
    only includes our desired data set.
    """
    raw_df = pd.read_csv(run_log_csv_path)
    last_to_skip = (
        pd.Series(range(len(raw_df))).where(raw_df["time"] == "time", -1).max()
    )
    trimmed_df = raw_df.iloc[(last_to_skip + 1) :, :]

    # There is a variable time distance between consecutive timestamps, and no points with null
    # values in between any two points, no matter how far apart their timestamps are.  If no null
    # null valued points fall between two points, Dygraph will implicitly interpolate a line
    # segment between the two values.  In order to reveal gaps in the actual data set, we need to
    # introduce one or more null values when two points are sufficiently far apart.
    #
    # Identify the rows that qcut() places in a quantile that is wider than the gap tolerance
    # threshold.  Examine each of these records to test whether its point is more than threshold
    # from the left and/or right boundaries.  Insert a gap point halfway between that point and
    # each boundary that is more than threshold distant.
    trimmed_df.loc[:, "time"] = pd.to_datetime(trimmed_df["time"])
    trimmed_df = trimmed_df.set_index("time", drop=False)
    trimmed_df["interval"] = pd.qcut(trimmed_df["time"], q=len(trimmed_df))
    trimmed_df["span_duration"] = trimmed_df["interval"].apply(
        lambda x: (x.right - x.left).seconds
    )

    large_df = trimmed_df[trimmed_df["span_duration"] > GAP_TOLERANCE]

    left_split = gen_left_only_split(GAP_TOLERANCE)
    large_left_nulls = large_df.apply(left_split, axis=1)
    large_left_index = pd.DatetimeIndex(large_left_nulls)
    large_left_nulls = pd.DataFrame(
        {"time": large_left_nulls.tolist()}, index=large_left_index
    )
    large_left_nulls = large_left_nulls[large_left_nulls["time"] != NO_DATE]

    right_split = gen_right_only_split(GAP_TOLERANCE)
    large_right_nulls = large_df.apply(right_split, axis=1)
    large_right_index = pd.DatetimeIndex(large_right_nulls)
    large_right_nulls = pd.DataFrame(
        {"time": large_right_nulls.tolist()}, index=large_right_index
    )
    large_right_nulls = large_right_nulls[large_right_nulls["time"] != NO_DATE]

    # Concatenate the null records to the original data frame, resort, and return
    merged_df = pd.concat([trimmed_df, large_left_nulls, large_right_nulls])
    return merged_df.sort_index()


def get_run_log_data_rows(raw_df, picked_columns, time_data):
    next_column = "time"
    data = {next_column: time_data}
    for next_column in picked_columns:
        data[next_column.header] = raw_df[next_column.header].map(next_column.parser)
    order = [next_column.header for next_column in picked_columns]
    order.insert(0, "time")
    df = pd.DataFrame(data=data, columns=order)
    return [[value for value in row_pair[1]] for row_pair in df.iterrows()]


def get_run_log_data_labels(picked_columns):
    ret_val = [meta.legend for meta in picked_columns]
    ret_val.insert(0, "Time (seconds)")
    return ret_val


def execute(archive_path, output_path, archive_type):
    files_config = find_purification_files(archive_path, required=set(["libPrep_log"]))
    raw_df = load_plan_log_csv(files_config["libPrep_log"])

    time_zero = raw_df["time"][0]
    time_axis = raw_df["time"].map(lambda x: (x - time_zero).total_seconds())

    run_log_temp_data = {
        "rows": get_run_log_data_rows(raw_df, TARGET_TEMP_FIELDS, time_axis),
        "labels": get_run_log_data_labels(TARGET_TEMP_FIELDS),
    }
    run_log_fan_data = {
        "rows": get_run_log_data_rows(raw_df, TARGET_FAN_FIELDS, time_axis),
        "labels": get_run_log_data_labels(TARGET_FAN_FIELDS),
    }
    run_log_misc_data = {
        "rows": get_run_log_data_rows(raw_df, TARGET_MISC_FIELDS, time_axis),
        "labels": get_run_log_data_labels(TARGET_MISC_FIELDS),
    }

    write_results_from_template(
        {
            "time_zero": time_zero.timestamp(),
            "gap_tolerance": GAP_TOLERANCE,
            "charts": [
                {
                    "height": 640,
                    "id_prefix": "temp",
                    "title": SafeString("Temperature (&deg;C)"),
                    "colors": [
                        "rgb(178,152,106)",
                        "rgb(209,147,232)",
                        "rgb(230,210,40)",
                        "rgb(109,200,196)",
                        "rgb(159,233,65)",
                        "rgb(200,69,232)",
                        "rgb(88,227,157)",
                        "rgb(209,242,88)",
                        "rgb(36,213,110)",
                        "rgb(205,162,227)",
                        "rgb(79,136,240)",
                        "rgb(52,167,78)",
                        "rgb(208,150,69)",
                        "rgb(47,152,194)",
                        "rgb(213,59,179)",
                        "rgb(176,199,102)",
                        "rgb(248,23,124)",
                        "rgb(124,138,216)",
                    ],
                    "raw_data": json.dumps(run_log_temp_data).replace("NaN", "null"),
                },
                {
                    "height": 280,
                    "id_prefix": "fan",
                    "title": "Fan (rpm) and Flow (spm) Rates",
                    "colors": [
                        "rgb(220,68,185)",
                        "rgb(57,146,151)",
                        "rgb(31,199,104)",
                        "rgb(100,167,236)",
                    ],
                    "raw_data": json.dumps(run_log_fan_data).replace("NaN", "null"),
                },
                {
                    "height": 280,
                    "id_prefix": "misc",
                    "title": "Miscellaneous",
                    "colors": [
                        "rgb(54,196,102)",
                        "rgb(220,64,182)",
                        "rgb(110,172,232)",
                    ],
                    "raw_data": json.dumps(run_log_misc_data).replace("NaN", "null"),
                },
            ],
        },
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )
    # Write out status and return
    return print_info("See results for flow, fan, and temperature plots.")


if __name__ == "__main__":
    archive_path_arg, output_path_arg, archive_type_arg = sys.argv[1:4]
    execute(archive_path_arg, output_path_arg, archive_type_arg)
