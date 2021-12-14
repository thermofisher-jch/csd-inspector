from dependency_injector import containers, providers

from reports.diagnostics.common.core_csa.debug import DebugLogParser
from reports.diagnostics.common.core_csa.explog import ExpLogParser
from reports.diagnostics.common.inspector_utils import read_explog


class CsaCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # These dependencies are intended for the activating instrument type to supply path information
    # regarding where it keeps its authoritative copy of `explog_final.txt` and `debug`.  We use
    # Dependency for this contract and not Configuration because, while these are values and values
    # are more strongly associated with Configuration, the more salient detail is the fact that
    # the contract by which these value are assigned is between this Container and the outer
    # embedding Container, and is therefore a detail that is assigned while executing code as that
    # "parent" (for the sake of Tournament hierarchical references) Container.  Configuration, in
    # contract, deals with values that are assigned from a pre-workflow human-operated function
    # just prior to the target Container's flow control will receive a handoff.
    explog_path = providers.Dependency()
    debug_log_path = providers.Dependency()

    # Factory functions without positional dependency arguments, meant for reuse when constructing
    # explogs for additional nested subsystems within a root CSA
    explog_parser_factory = providers.Factory(ExpLogParser)
    debug_log_parser_factory = providers.Factory(DebugLogParser)

    # Fully configured singleton.  Meant for collaborative access to the root explog for a CSA.
    # One global instance, shared across all consuming stakeholders.
    explog_parser = providers.Singleton(
        explog_parser_factory, config.archive_root, explog_path
    )
    debug_log_parser = providers.Singleton(
        debug_log_parser_factory, explog_parser, debug_log_path
    )
