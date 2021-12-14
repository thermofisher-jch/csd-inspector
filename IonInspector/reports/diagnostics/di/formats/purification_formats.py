from dependency_injector import containers, providers

from reports.diagnostics.common.core_csa.enrich import ErrorLogReportEnricher
from reports.diagnostics.common.quant_csa.parser import QuantParserFactory
from reports.diagnostics.common.quant_csa.enrich import (
    QuantSummaryEnricher,
    ConsumableLotsSummaryEnricher,
)
from reports.diagnostics.common.reporting import ModelEnricherProvider
from reports.diagnostics.common.run_log_csa import (
    COLUMN_PARSE_CONFIG,
    RUN_REPORT_ENRICHMENT_META,
    TIME_ELAPSED_DISPLAY_LABEL,
    TIME_COLUMN_KEY,
)
from reports.diagnostics.common.run_log_csa.enrich import LibPrepReportEnricher
from reports.diagnostics.common.run_log_csa.parser import LibPrepRunParser


class PurificationParsersContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Injection binding to facilitate unit test based overriding
    column_parse_config = providers.Dict(COLUMN_PARSE_CONFIG)
    time_column_key = providers.Object(TIME_COLUMN_KEY)
    time_elapsed_display_label = providers.Object(TIME_ELAPSED_DISPLAY_LABEL)

    # User configuration-based override for runtime control, not just unit testing
    gap_tolerance = config.gap_tolerance.as_int()

    run_log_parser = providers.Singleton(
        LibPrepRunParser,
        column_configs=column_parse_config,
        gap_tolerance=gap_tolerance,
        time_column=time_column_key,
        time_display_label=time_elapsed_display_label,
    )
    quant_parser_factory = providers.Singleton(QuantParserFactory)


class PurificationEnrichmentContainer(containers.DeclarativeContainer):
    # Injection binding to facilitate unit test based overriding
    run_report_enrichment_meta = providers.Object(RUN_REPORT_ENRICHMENT_META)

    error_log_report_enricher = ModelEnricherProvider(ErrorLogReportEnricher)
    run_log_report_enricher = ModelEnricherProvider(
        LibPrepReportEnricher, run_report_enrichment_meta
    )
    quant_summary_enricher = ModelEnricherProvider(QuantSummaryEnricher)
    consumable_lots_summary_enricher = ModelEnricherProvider(
        ConsumableLotsSummaryEnricher
    )
