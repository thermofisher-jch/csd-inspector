import pandas as pd

from reports.diagnostics.common.run_log_csa import (
    TIME_ELAPSED_DISPLAY_LABEL,
    TIME_COLUMN_KEY,
)
from reports.diagnostics.common.run_log_csa.types import LibPrepBatchRunModel


class LibPrepRunParser:
    """
    The csv may begin before the target run, but it will not run beyond the its end.
    Partial data collection from before the actual run manifests as extra data followed
    by additional header rows.  To filter it out, we ask Pandas to re-index the CSV using
    the time column and the original line-number index column.   This lets use query the
    index for all 'time' column rows with a value that matches 'time'.  The largest such
    match bears the line number of the last row before real data began,

    Once we have found the last line we want to remove, we return to the original loaded
    CSV file-sourced DataFrame and remove the first N rows, where N was found as described
    above.  The transformed DataFrame returned cn now be safely re-indexed by only the
    time column, since it will no longer have duplicate copies of the string 'time', and
    only includes our desired data set.

    There is a variable time distance between consecutive timestamps, and no points with null
    values in between any two points, no matter how far apart their timestamps are.  If no null
    null valued points fall between two points, Dygraph will implicitly interpolate a line
    segment between the two values.  In order to reveal gaps in the actual data set, we need to
    introduce one or more null values when two points are sufficiently far apart.

    Identify the rows that qcut() places in a quantile that is wider than the gap tolerance
    threshold.  Examine each of these records to test whether its point is more than threshold
    from the left and/or right boundaries.  Insert a gap point halfway between that point and
    each boundary that is more than threshold distant.
    """

    def __init__(
        self,
        column_configs=None,
        gap_tolerance=45,
        time_column=TIME_COLUMN_KEY,
        time_display_label=TIME_ELAPSED_DISPLAY_LABEL,
    ):
        self._column_configs = column_configs
        self._gap_tolerance = pd.Timedelta(seconds=gap_tolerance)
        self._time_display_label = time_display_label
        self._time_column = time_column
        # TODO: Time display label belongs in enrichmnet, as does the display label present here
        #       with the column config meta.  This is retained for historical reasons to minimize
        #       the refactoring done at the time this was modularized for reuse.

    # def _old_gap_split(self):
    #     trimmed_df = self._trimmed_df
    #     trimmed_df["interval"] = pd.qcut(trimmed_df["time"], q=len(trimmed_df))
    #     trimmed_df["span_duration"] = trimmed_df["interval"].apply(
    #         lambda x: (x.right - x.left).seconds
    #     )
    #
    #     large_df = trimmed_df[trimmed_df["span_duration"] > self._gap_tolerance]
    #
    #     left_split = gen_left_only_split(self._gap_tolerance)
    #     large_left_nulls = large_df.apply(left_split, axis=1)
    #     large_left_index = pd.DatetimeIndex(large_left_nulls)
    #     large_left_nulls = pd.DataFrame(
    #         {"time": large_left_nulls.tolist()}, index=large_left_index
    #     )
    #     large_left_nulls = large_left_nulls[large_left_nulls["time"] != NO_DATE]
    #
    #     right_split = gen_right_only_split(self._gap_tolerance)
    #     large_right_nulls = large_df.apply(right_split, axis=1)
    #     large_right_index = pd.DatetimeIndex(large_right_nulls)
    #     large_right_nulls = pd.DataFrame(
    #         {"time": large_right_nulls.tolist()}, index=large_right_index
    #     )
    #     large_right_nulls = large_right_nulls[large_right_nulls["time"] != NO_DATE]
    #
    #     Concatenate the null records to the original data frame, resort, and return
    # self._merged_df = pd.concat([trimmed_df, large_left_nulls, large_right_nulls])
    # self._merged_df.sort_index()
    # self._time_zero = self._merged_df["time"][0]
    # self._time_axis = self._merged_df["time"].map(
    #     lambda x: (x - self._time_zero).total_seconds()
    # )

    def _parse_csv_file(self, run_log_csv_path):
        raw_df = pd.read_csv(run_log_csv_path)
        last_to_skip = (
            pd.Series(range(len(raw_df)))
            .where(raw_df[self._time_column] == self._time_column, -1)
            .max()
        )
        raw_df = raw_df.iloc[(last_to_skip + 1) :, :]
        raw_df.loc[:, self._time_column] = pd.to_datetime(raw_df[self._time_column])
        return raw_df.set_index(self._time_column, drop=False)

    def _break_up_gaps(self, trimmed_df):
        # Add the time index of each row's prior row as its "time_last" column
        trimmed_df.loc[1:, "time_last"] = trimmed_df.loc[:, self._time_column].tolist()[
            0:-1
        ]
        # Add the difference between each row's current and previous times as is "delta" column
        trimmed_df.loc[:, "delta"] = (
            trimmed_df[self._time_column] - trimmed_df["time_last"]
        )
        # Compute a series of timestamps such that each falls between the current and row's time
        # and any preceding row's time.  Call this new column "time_between"
        gap_rows = pd.qcut(trimmed_df[self._time_column], q=len(trimmed_df))
        trimmed_df = trimmed_df.join(
            pd.DataFrame(
                [x.left for x in gap_rows.values.tolist()],
                index=gap_rows.index,
                columns=["time_between"],
            )
        )
        # Select rows whose "delta" is large enough to justify calling a gap at its "time_between"
        # moment.  Create an index from the "time_between" values of each such row in order to
        # create a filler point with null values in each sensor's values column at each such
        # time_between location.
        gap_rows = (
            trimmed_df[trimmed_df["delta"] > self._gap_tolerance]["time_between"]
            .to_frame()
            .set_index("time_between", drop=False)
        )
        gap_rows["time"] = gap_rows["time_between"]
        # Concatenate trimmed_df, with actual data rows, with gap_flows then sort the
        # result for chronological ordering of data values and gap markers.
        return (
            pd.concat([trimmed_df, gap_rows])
            .drop({"time_last", "delta", "time_between"}, axis=1)
            .sort_index()
        )

    def parse_file(self, instance_name, run_log_csv_path):
        """
        Given the collection_name of an entry in the column_configs
        dictionary, retrieve its list of ColumnParserConfig objects and use
        them to extract their corresponding TimeSeriesCollection which
        presents data from the Pandas data frame corresponding to
        the ColumnParserConfig definitions.

        TODO: This is the WRONG place to be applying the map from access key to
              display name.  That is an activity that belongs to enrichment

        Parameters
        ----------
        instance_name    Display name corresponding to the source file
        run_log_csv_path Source file to parse and load into a metrics DataFrame

        Returns
        -------
        A TimeSeriesData which captures the instance_name, a DataFrame with extracted
        time series from run_log_csv_path, and a copy of the gap_tolerance value used.
        """
        trimmed_df = self._parse_csv_file(run_log_csv_path)
        prepared_df = self._break_up_gaps(trimmed_df)
        time_zero = prepared_df[self._time_column][0]
        data = [
            {
                (metric_name, col_meta.legend): prepared_df[col_meta.header]
                .map(col_meta.decoder)
                .tolist()
                for col_meta in sensor_columns
            }
            for (metric_name, sensor_columns) in self._column_configs.items()
        ]
        data[0].update(data[1])
        data = data[0]
        data[(self._time_column, self._time_display_label)] = prepared_df[
            self._time_column
        ].map(lambda x: (x - time_zero).total_seconds())
        data = pd.DataFrame(data, index=prepared_df.index)
        return LibPrepBatchRunModel(
            instance_name, data, self._gap_tolerance, time_zero, self._time_column
        )

        # data = {"time": self._time_axis}
        # for next_column in picked_columns:
        #     data[next_column.header] = self._prepared_df[next_column.header] \
        #         .map(next_column.parser)
        # order = [next_column.header for next_column in picked_columns]
        # order.insert(0, "time")
        # df = pd.DataFrame(data=data, columns=order)
        # return [[value for value in row_pair[1]] for row_pair in df.iterrows()]
        #     labels = [next_column.legend for next_column in sensor_columns]
        #     labels.insert(0, "Time (seconds)")
        #     data = [
        #         self._prepared_df[next_column.header].map(next_column.decoder)
        #         for next_column in picked_columns
        #     ]
        #     data.insert(0, self._time_axis)

    # def get_run_log_data_labels(picked_columns):
    #     ret_val = [meta.legend for meta in picked_columns]
    #     ret_val.insert(0, "Time (seconds)")
    #     return ret_val


# def gen_left_only_split(threshold):
#     def left_short_split(x):
#         left_delta = x["time"] - x["interval"].left
#         if left_delta.seconds > threshold:
#             return x["interval"].left + (left_delta / 2)
#         else:
#             return NO_DATE
#
#     return left_short_split
#
#
# def gen_right_only_split(threshold):
#     def right_short_split(x):
#         right_delta = x["interval"].right - x["time"]
#         if right_delta.seconds > threshold:
#             return x["time"] + (right_delta / 2)
#         else:
#             return NO_DATE
#
#     return right_short_split
#
#
# def short_split(x):
#     left_delta = x["time"] - x["interval"].left
#     right_delta = x["interval"].right - x["time"]
#     if left_delta > right_delta:
#         return x["interval"].left + (left_delta / 2)
#     else:
#         return x["time"] + (right_delta / 2)
