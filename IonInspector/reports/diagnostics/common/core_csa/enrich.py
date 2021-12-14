import pandas as pd

from reports.diagnostics.common import inspector_utils
from reports.diagnostics.common.core_csa.values import (
    EXPLOG_ERROR_META,
    DEBUG_BEFORE_META,
    DEBUG_DURING_META,
    DEBUG_AFTER_META,
)
from reports.diagnostics.common.reporting import IModelEnricher


class ErrorLogReportEnricher(IModelEnricher):
    def enrich_model(self, source_context):
        return {
            "batches": [
                self._enrich_batch_logs(batch_logs) for batch_logs in source_context
            ]
        }

    def get_summary_meta(self, source_model, report_model):
        for batch_model in source_model:
            if batch_model.has_debug_errors:
                return inspector_utils.print_alert(
                    "Experiment errors found in explog or debug"
                )
        return inspector_utils.print_ok("No experiment or debug errors found")

    def _enrich_batch_logs(self, batch_logs):
        before_debug = batch_logs.before_debug_errors
        during_debug = batch_logs.during_debug_errors
        after_debug = batch_logs.after_debug_errors
        experiment_log = (batch_logs.experiment_errors,)

        instances = []
        if len(before_debug) > 0:
            instances.append(
                self._define_error_table(
                    batch_logs.batch_label + "-pre",
                    DEBUG_BEFORE_META,
                    batch_logs.before_debug_errors,
                ),
            )
        if len(experiment_log) > 0:
            instances.append(
                self._define_error_table(
                    batch_logs.batch_label + "-exp",
                    EXPLOG_ERROR_META,
                    batch_logs.experiment_errors,
                ),
            )
        if len(during_debug) > 0:
            instances.append(
                self._define_error_table(
                    batch_logs.batch_label + "-debug",
                    DEBUG_DURING_META,
                    batch_logs.during_debug_errors,
                ),
            )
        if len(after_debug) > 0:
            instances.append(
                self._define_error_table(
                    batch_logs.batch_label + "-post",
                    DEBUG_AFTER_META,
                    batch_logs.after_debug_errors,
                )
            )

        return {
            "id_prefix": batch_logs.batch_label,
            "batch_label": "Errors for " + batch_logs.batch_label,
            "instances": instances,
        }

    def _define_error_table(self, id_prefix, label_meta, data_rows):
        temp_df = pd.DataFrame(data_rows, columns=label_meta["column_labels"])
        context = label_meta.copy()
        context["id_prefix"] = id_prefix
        context["table_html"] = temp_df.to_html(
            justify="center",
            bold_rows=False,
            header=True,
            index=False,
            classes="card-body table table-bordered table-striped",
        )
        return context
