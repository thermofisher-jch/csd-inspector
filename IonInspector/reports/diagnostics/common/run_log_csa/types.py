from kombu.utils import symbol_by_name


class LibPrepMetricSpec:
    def __init__(self, metric_key_id, display_name, chart_height, sensor_colors):
        self._metric_key_id = metric_key_id
        self._display_name = display_name
        self._chart_height = chart_height
        self._sensor_colors = sensor_colors

    @property
    def metric_key_id(self):
        return self._metric_key_id

    @property
    def display_name(self):
        return self._display_name

    @property
    def chart_height(self):
        return self._chart_height

    @property
    def sensor_colors(self):
        return self._sensor_colors


class LibPrepEnrichmentMeta:
    """
    Root metadata object describing how to enrich parser output in order to prepare
    it as a context for display.  Provides the display label for the common time axis and
    groups the individual sensor fields by their common unit of measure in order to describe
    chart properties they share as a group.
    """

    def __init__(self, elapsed_time_label, metric_spec_list):
        self._elapsed_time_label = elapsed_time_label
        self._metric_spec_list = metric_spec_list

    @property
    def elapsed_time_label(self):
        return self._elapsed_time_label

    @property
    def metric_spec_list(self):
        return self._metric_spec_list.copy()


class LibPrepColumnSpec:
    """
    Metadata type at the level of parser task definition
    TODO: The legend display name does not belong here--it is an attribute of enrichment
          for display, not a fundamental property of the data access parser, which should
          draw its contractual boundary at the access key that enrichment will decorate
          further for display.

    @param header The string used to match this data column's header in
                  lib_prepRun.log
    @param legend The string used to present this data column's header in
                  a chart's legend
    @param decoder A callable that can be used to parse the string form of a data value
                   to its native data_type, given as <moduleFQN>:<attributeName>
                   (e.g. "__builtin__:float" or "reports.diagnostics.utility.parsers:pars_bibo"
    """

    def __init__(self, header, legend, decoder):
        self._header = header
        self._legend = legend
        self._decoder = symbol_by_name(decoder)

    @property
    def header(self):
        return self._header

    @property
    def legend(self):
        return self._legend

    @property
    def decoder(self):
        return self._decoder


class LibPrepBatchRunModel:
    """
    Data Class capturing an "instance" associated collection of time series data.  The
    time series are captured in a data frame that is row indexed by time, and column indexed
    by a two-level MultiIndex.  The top-most level of the column index groups time series by
    a utility measurement type, such as 'Temperature' or 'Frequency'.  Column index's nested
    level is named according to which sensor that column's rows contain observed measurements
    from.
    E.g.:
       Type      Freq    Temp
       Sensor    r  s    a  b  c
       time1     9  5    1  2  2
       time2     1  4    2  4  2
       time3     1  3    3  6  6
       time4     4  2    4  8  4
    """

    def __init__(self, instance_label, data_frame, gap_tolerance, time_zero, time_key):
        self._instance_label = instance_label
        self._data_frame = data_frame
        self._gap_tolerance = gap_tolerance
        self._time_zero = time_zero
        self._time_key = time_key

    @property
    def instance_label(self):
        return self._instance_label

    @property
    def metric_names(self):
        return self._data_frame.columns.levels[0].tolist()[1:]

    @property
    def time_zero(self):
        return self._time_zero

    @property
    def time_index(self):
        return self._data_frame.index.tolist()

    @property
    def time_key(self):
        return self._time_key

    @property
    def gap_tolerance(self):
        return self._gap_tolerance

    def sensor_name_list(self, metric_type):
        """
        Given a metric type name list all sensor names with data available for that metric type.

        Parameters
        ----------
        metric_type :: identifier key for a family of observed time series data that all share
                       a common data type, such as Temperature or Rotational Frequency.

        Returns
        -------
        A list of sensor names with data for named metric type.
        """
        return self._data_frame[metric_type].columns.tolist()

    def sensor_data_list(self, metric_type, sensor_name):
        """
        Given a metric type and a sensor name under named metric, return time series data
        for only named sensor.
        Parameters
        ----------
        metric_type :: identifier key for a family of observed time series data that all share
                       a common data type, such as Temperature or Rotational Frequency.
        sensor_name :: name of a sensor of a type matching metric_type

        Returns
        -------
        A list with time series of observations for named sensor.
        """
        return self._data_frame[metric_type][sensor_name].tolist()

    def metric_data_lists(self, metric_type):
        """
        Given a metric type name, return a data frame with multiple columns but only one
        level of index per column, where that index contains the sensor name a given column
        contains the time series of observations for and every column is in units corresponding
        to the named metric type.

        Parameters
        ----------
        metric_type :: identifier key for a family of observed time series data that all share
                       a common data type, such as Temperature or Rotational Frequency.

        Returns
        -------
        A list of lists in the same order by sensor as the names returned by
        sensor_name_lists() when passed the same metric_type as a parameter.
        """
        metric_df = self._data_frame[metric_type]
        return [metric_df[name].tolist() for name in metric_df.columns]

    def metric_data_dict(self, metric_type):
        """
        Given a metric type name, return a dictionary with a list of data for each sensor
        reported for the given metric_type argument, with each list keyed by the name of
        its associated sensor.

        Parameters
        ----------
        metric_type :: identifier key for a family of observed time series data that all share
                       a common data type, such as Temperature or Rotational Frequency.

        Returns
        -------
        A dictionary keyed by sensor name where each value is the data series for the sensor
        named by its dictionary key expressed as a list.
        """
        metric_df = self._data_frame[metric_type]
        return {name: metric_df[name].tolist() for name in metric_df.columns}
