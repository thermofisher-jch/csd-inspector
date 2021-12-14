from dependency_injector import containers, providers
from django.template import engines, Engine, Template
from django.template.backends.django import DjangoTemplates

from reports.diagnostics.common.reporting import ISourceLoader, IModelEnricher
from reports.diagnostics.common.reporting.runner import RenderReportRunner
from reports.diagnostics.common.reporting.types import RenderReportRunnerProvider


class RenderReportContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    template_engine = providers.Dependency(instance_of=DjangoTemplates)
    source_loader = providers.Dependency(instance_of=ISourceLoader)
    display_enricher = providers.Dependency(instance_of=IModelEnricher)
    template_name = providers.Dependency(instance_of=str)

    django_template = template_engine.provided.get_template.call(template_name)

    # TODO: Invert the flow control here.  Let the ISourceLoader and IModelEnricher act as
    #       push-based publishers and wire the chain of flow by subscribing each artifact
    #       to its predecessor.  This could be more appropriate when we introduce Kafka as
    #       a message broker.
    report_runner = RenderReportRunnerProvider(
        RenderReportRunner,
        source_loader,
        display_enricher,
        django_template,
        config.output_directory,
    )

    # process_report = providers.Factory(
    #     lambda generator, input_dir, output_dir: generator.process_report(
    #         input_dir, output_dir
    #     ),
    #     report_generator,
    # )
    # process_report = report_runner.provided.process_report
