import json

import numpy as np

from reports.diagnostics.common.inspector_utils import print_info
from reports.diagnostics.common.reporting import IModelEnricher
from reports.diagnostics.common.run_log_csa import TEMPERATURE_METRIC, FREQUENCY_METRIC


class LibPrepReportEnricher(IModelEnricher):
    def __init__(self, enrichment_metadata=None):  # , template_path="./template.html"):
        IModelEnricher.__init__(self)
        self._metric_metadata = enrichment_metadata.metric_spec_list or {}
        self._elapsed_time_label = enrichment_metadata.elapsed_time_label

    def enrich_model(self, data_model):
        """
        Parameters
        ----------
        data_model Either a single TimeSeriesDataModel or a list of multiple TimeSeriesDataModels

        Returns
        -------
        A context dictionary based on the content of data_model, but transformed to fold in
        contextual state required for HTML report rendering.
        """
        if type(data_model) != list:
            data_model = [data_model]
        return dict(
            instances=[self._enrich_instance(model) for model in data_model],
        )

    def get_summary_meta(self, source_model, reporting_model):
        return print_info("See results for flow, fan, and temperature plots.")

    def _enrich_instance(self, data_instance):
        """
        Parameters
        ----------
        data_model A TimeSeriesData instance with all data content to report
        output_path Path to the HTML file where rendered content is to be written
        """
        time_zero = data_instance.time_zero.timestamp()
        temp_metric = self._metric_metadata[TEMPERATURE_METRIC]
        run_log_temp_data = {
            "labels": data_instance.sensor_name_list(TEMPERATURE_METRIC),
            "rows": data_instance.metric_data_lists(TEMPERATURE_METRIC),
        }
        fan_metric = self._metric_metadata[FREQUENCY_METRIC]
        run_log_fan_data = {
            "labels": data_instance.sensor_name_list(FREQUENCY_METRIC),
            "rows": data_instance.metric_data_lists(FREQUENCY_METRIC),
        }
        elapsed_index = [t.timestamp() - time_zero for t in data_instance.time_index]

        return {
            "time_zero": time_zero,
            "gap_tolerance": data_instance.gap_tolerance,
            "charts": [
                {
                    "height": temp_metric.chart_height,
                    "id_prefix": TEMPERATURE_METRIC,
                    "title": temp_metric.display_name,
                    "colors": temp_metric.sensor_colors,
                    "raw_data": json.dumps(
                        self._reshape_data(run_log_temp_data, elapsed_index)
                    ).replace("NaN", "null"),
                },
                {
                    "height": fan_metric.chart_height,
                    "id_prefix": FREQUENCY_METRIC,
                    "title": fan_metric.display_name,
                    "colors": fan_metric.sensor_colors,
                    "raw_data": json.dumps(
                        self._reshape_data(run_log_fan_data, elapsed_index)
                    ).replace("NaN", "null"),
                },
            ],
        }

    def _reshape_data(self, raw_data, elapsed_index):
        labels = [label for label in raw_data["labels"]]
        labels.insert(0, self._elapsed_time_label)
        columns = [column for column in raw_data["rows"]]
        columns.insert(0, elapsed_index)
        np_columns = np.array(columns)
        return {"rows": np_columns.transpose(1, 0).tolist(), "labels": labels}
