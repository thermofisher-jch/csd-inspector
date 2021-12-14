import abc

from dependency_injector import containers, providers

from reports.diagnostics.common.reporting.types import ISourceLoader, IModelEnricher


# Allow SourceLoaderContainers to have dependencies
# SourceLoaderProvider.register(providers.Dependency)
#
#
# class SourceLoaderContainer(containers.DeclarativeContainer):
#     provider_type = SourceLoaderProvider
#
#
# class ModelEnrichmentProvider(providers.Dependency):
#     instance_of = IModelEnricher
#
#
# class ModelEnrichmentContainer(containers.DeclarativeContainer):
#     provider_type = ModelEnrichmentProvider
