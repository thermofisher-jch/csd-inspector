import os

from dependency_injector import containers, providers

from reports.diagnostics.common.reporting import (
    SourceLoaderProvider,
    PURIFICATION_RUN_LOG_REPORT,
    PURIFICATION_ERROR_LOG_REPORT,
    PURIFICATION_LOT_SUMMARY,
    PURIFICATION_QUANT_SUMMARY,
)
from reports.diagnostics.common.reporting.purification import (
    StandaloneArchiveFeatures,
    StandalonePurificationQuantSummaryLoader,
    StandalonePurificationRunLogLoader,
    StandalonePurificationErrorLogLoader,
)
from reports.diagnostics.di.formats import (
    CsaCoreContainer,
    PurificationParsersContainer,
    PurificationEnrichmentContainer,
)
from reports.diagnostics.di.reports.runner import RenderReportContainer
from reports.diagnostics.di.reports.templates import TemplateEngineContainer


class StandalonePurificationInstrumentTypeContainer(containers.DeclarativeContainer):
    """
    Application-tier container specific to standalone purification.  Application-tier means that
    it is meant to be instantiated without providing any dependencies because it knows how to
    create and wire all containers it needs
    """

    config = providers.Configuration()
    archive_root = config.csa_core.archive_root
    explog_path = providers.Callable(
        lambda archive_root: os.path.join(archive_root, "explog_final.txt"),
        archive_root,
    )
    debug_log_path = providers.Callable(
        lambda archive_root: os.path.join(archive_root, "debug"), archive_root
    )

    # Instrument type agnostic containers for distributing common libraries
    csa_core_container = providers.Container(
        CsaCoreContainer,
        config=config.csa_core,
        explog_path=explog_path,
        debug_log_path=debug_log_path,
    )
    purification_parsers_container = providers.Container(
        PurificationParsersContainer, config=config.purification
    )
    purification_enrichment_container = providers.Container(
        PurificationEnrichmentContainer
    )
    template_engine_container = providers.Container(TemplateEngineContainer)

    # ArchiveFeatures is an instrument-type specific singleton that encapsulate how that type
    # determines where source content files are found and what features its various versions
    # support so reports may correctly reflect that evolution.
    archive_features = providers.Singleton(
        StandaloneArchiveFeatures, archive_root, csa_core_container.explog_parser
    )

    # Instrument type specific source assembly
    error_log_source = SourceLoaderProvider(
        StandalonePurificationErrorLogLoader,
        csa_core_container.debug_log_parser,
        csa_core_container.explog_parser,
    )
    run_log_source = SourceLoaderProvider(
        StandalonePurificationRunLogLoader,
        archive_features,
        purification_parsers_container.run_log_parser,
        csa_core_container.explog_parser,
    )
    quant_summary_source = SourceLoaderProvider(
        StandalonePurificationQuantSummaryLoader,
        archive_features,
        purification_parsers_container.quant_parser_factory,
        csa_core_container.explog_parser,
    )

    # Report Containers from here on below.  If a given report type is produced by a Diagnostic
    # that is scheduled for multiple instrument types under the 1.x Inspector architecture, then
    # it must use the same property name in each such instrument type's root container.  This
    # restriction will be lifted in 2.x.

    purification_error_log_report = providers.Container(
        RenderReportContainer,
        config=config.csa_core,
        source_loader=error_log_source,
        display_enricher=purification_enrichment_container.error_log_report_enricher,
        template_engine=template_engine_container.template_engine,
        template_name="multi_batch_error_log.html",
    )

    purification_run_log_report = providers.Container(
        RenderReportContainer,
        config=config.csa_core,
        source_loader=run_log_source,
        display_enricher=purification_enrichment_container.run_log_report_enricher,
        template_engine=template_engine_container.template_engine,
        template_name="multi_batch_run_log.html",
    )

    purification_consumable_lots_report = providers.Container(
        RenderReportContainer,
        config=config.csa_core,
        source_loader=quant_summary_source,
        display_enricher=purification_enrichment_container.consumable_lots_summary_enricher,
        template_engine=template_engine_container.template_engine,
        template_name="consumable_lots_results.html",
    )

    purification_quant_summary_report = providers.Container(
        RenderReportContainer,
        config=config.csa_core,
        source_loader=quant_summary_source,
        display_enricher=purification_enrichment_container.quant_summary_enricher,
        template_engine=template_engine_container.template_engine,
        template_name="quant_summary_results.html",
    )

    aggregate_report_runner_factory = providers.FactoryAggregate(
        {
            PURIFICATION_RUN_LOG_REPORT: purification_run_log_report.report_runner,
            PURIFICATION_ERROR_LOG_REPORT: purification_error_log_report.report_runner,
            PURIFICATION_LOT_SUMMARY: purification_consumable_lots_report.report_runner,
            PURIFICATION_QUANT_SUMMARY: purification_quant_summary_report.report_runner,
        }
    )

    render_selected_report = providers.Singleton(
        aggregate_report_runner_factory, config.csa_core.selected_report_name
    )
    process_report = render_selected_report.provided.process_report.call()
