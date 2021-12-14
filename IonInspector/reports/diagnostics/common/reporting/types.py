import abc

# Known report_template keys
from dependency_injector import providers

from reports.diagnostics.common import inspector_utils

PURIFICATION_CONSUMABLE_LOTS_DIAGNOSTIC = "purification_consumable_lots"
PURIFICATION_QUANT_SUMMARY_DIAGNOSTIC = "purification_quant_summary"
PURIFICATION_RUN_LOG_DIAGNOSTIC = "purification_run_log"


class ISourceLoader:
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def source_model(self):
        pass


class SourceLoaderProvider(providers.Singleton):
    provided_type = ISourceLoader


class IModelEnricher:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def enrich_model(self, source_context):
        """
        Call signature for a singleton method that expects a particular kind of DataClass, Dict, or
        List produced by an ISourceLoader and returns an augmented object with additional metadata
        such that it can be used as the context object for a particular report template.

        This interface is not strongly typed and has no reusable functionality.  It only exists as
        an organization aid to help developers document the input/output pairings without repeating
        these common details from case to case.

        Parameters
        ----------
        source_context Output from a compatible ISourceLoader

        Returns
        -------
        Content dictionary that will be passed to associated Django Template's render() method.
        """
        raise NotImplementedError()

    def get_summary_meta(self, source_context, display_context):
        """
        Not abstract, this has a base default implementation

        Parameters
        ----------
        source_context Output from a compatible ISourceLoader

        Returns
        -------
        A Tuple formatted for Inspector's diagnostic `status` summary line default is used,
           an info message that reads 'See results for details.'

        """
        return inspector_utils.print_info("See results for details.")


class ModelEnricherProvider(providers.Singleton):
    provided_type = IModelEnricher


class IRenderReportRunner:
    """
    Activation interface for a utility object that wires to a compatible
    ISourceLoader/IModelEnricher/DjangoTemplate triad and orchestrates the
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def process_report(self, output_dir):
        pass


class RenderReportRunnerProvider(providers.Factory):
    provided_type = IRenderReportRunner
