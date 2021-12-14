import functools32

from reports.diagnostics.common.core_csa.types import BatchErrorsModel
from reports.diagnostics.common.reporting.types import ISourceLoader


class StandalonePurificationErrorLogLoader(ISourceLoader):
    def __init__(self, debug_parser, explog_parser):
        ISourceLoader.__init__(self)
        self._explog_parser = explog_parser
        self._debug_parser = debug_parser

    @property
    @functools32.lru_cache(maxsize=1)
    def source_model(self):
        explog_errors = self._explog_parser.error_log
        debug_errors = self._debug_parser.error_log
        return [BatchErrorsModel("Standalone", explog_errors, debug_errors)]


class StandalonePurificationQuantSummaryLoader(ISourceLoader):
    def __init__(self, archive_features, quant_parser_factory, explog_parser):
        ISourceLoader.__init__(self)
        self._archive_features = archive_features
        self._quant_parser_factory = quant_parser_factory
        self._explog_parser = explog_parser

    @property
    @functools32.lru_cache(maxsize=1)
    def source_model(self):
        quant_csv_path = self._archive_features.quant_summary_log
        return [self._quant_parser_factory.create_parser("Standalone", quant_csv_path)]


class StandalonePurificationRunLogLoader(ISourceLoader):
    def __init__(self, archive_features, run_log_parser, explog_parser):
        ISourceLoader.__init__(self)
        self._archive_features = archive_features
        self._run_log_parser = run_log_parser
        self._explog_parser = explog_parser

    @property
    @functools32.lru_cache(maxsize=1)
    def source_model(self):
        run_log_csv_path = self._archive_features.lib_prep_run_log
        return [self._run_log_parser.parse_file("Standalone", run_log_csv_path)]
