import json
import logging
import os
import traceback

from django.core.serializers.json import DjangoJSONEncoder

from reports.diagnostics.common import inspector_utils
from reports.diagnostics.common.reporting.types import IRenderReportRunner

LOGGER = logging.getLogger("RenderReportRunner")


class RenderReportRunner(IRenderReportRunner):
    def __init__(
        self,
        model_loader,
        display_enricher,
        report_template,
        output_directory,
        json_source_out="source.json",
        json_display_out="main.json",
        html_report_out="results.html",
    ):
        self._model_loader = model_loader
        self._display_enricher = display_enricher
        self._report_template = report_template
        self._output_directory = output_directory
        self._json_source_out = json_source_out
        self._json_display_out = json_display_out
        self._html_report_out = html_report_out

    def process_report(self):
        source_context = self._model_loader.source_model
        self._write_source_context(source_context)
        # Default metadata if none comes when enrichment yields template context.
        display_context = self._display_enricher.enrich_model(source_context)
        assert type(display_context) == dict
        self._write_display_context(display_context)
        html_content = self._report_template.render(display_context)
        self._write_html_report(html_content.encode("UTF-8"))
        summary_metadata = self._display_enricher.get_summary_meta(
            source_context, display_context
        )
        assert type(summary_metadata) == tuple
        return summary_metadata

    def _write_source_context(self, source_context):
        json_file = os.path.join(self._output_directory, self._json_source_out)
        try:
            with open(json_file, "w") as fp:
                json.dump(source_context, fp, cls=DjangoJSONEncoder)
        except Exception:
            LOGGER.exception(
                "Could not write source context json\n" + traceback.format_exc()
            )

    def _write_display_context(self, display_context):
        json_file = os.path.join(self._output_directory, self._json_display_out)
        try:
            with open(json_file, "w") as fp:
                json.dump(display_context, fp, cls=DjangoJSONEncoder)
        except Exception:
            LOGGER.exception(
                "Could not write display context json\n" + traceback.format_exc()
            )

    def _write_html_report(self, html_content):
        html_file = os.path.join(self._output_directory, self._html_report_out)
        try:
            with open(html_file, "w") as out:
                out.write(html_content)
        except Exception:
            LOGGER.exception("Failed to write HTML report\n" + traceback.format_exc())
