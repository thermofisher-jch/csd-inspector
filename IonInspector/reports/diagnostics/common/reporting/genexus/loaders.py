import os

import functools32

from reports.diagnostics.common.core_csa.types import BatchErrorsModel
from reports.diagnostics.common.reporting.types import ISourceLoader


class IntegratedPurificationErrorLogLoader(ISourceLoader):
    def __init__(self, archive_features, debug_parser_provider, explog_parser_provider):
        ISourceLoader.__init__(self)
        self._archive_features = archive_features
        self._debug_parser_provider = debug_parser_provider
        self._explog_parser_provider = explog_parser_provider

    @property
    @functools32.lru_cache(maxsize=1)
    def source_model(self):
        return [
            BatchErrorsModel(
                batch_subdir.batch_label,
                batch_subdir.explog_parser.error_log,
                batch_subdir.debug_log_parser.error_log,
            )
            for batch_subdir in self._archive_features.purification_batch_metadata
        ]


class IntegratedPurificationQuantSummaryLoader(ISourceLoader):
    def __init__(self, archive_features, quant_parser_factory):
        ISourceLoader.__init__(self)
        self._archive_features = archive_features
        self._quant_parser_factory = quant_parser_factory

    @property
    @functools32.lru_cache(maxsize=1)
    def source_model(self):
        return [
            self._quant_parser_factory.create_parser(
                quant_csv_batch.keys()[0], quant_csv_batch.values()[0]
            )
            for quant_csv_batch in self._archive_features.purification_quant_summaries
            if os.path.isfile(quant_csv_batch.values()[0])
        ]


class IntegratedPurificationRunLogLoader(ISourceLoader):
    def __init__(self, archive_features, run_log_parser):
        ISourceLoader.__init__(self)
        self._archive_features = archive_features
        self._run_log_parser = run_log_parser

    @property
    @functools32.lru_cache(maxsize=1)
    def source_model(self):
        return [
            self._run_log_parser.parse_file(
                lib_prep_batch.keys()[0], lib_prep_batch.values()[0]
            )
            for lib_prep_batch in self._archive_features.purification_run_logs
            if os.path.isfile(lib_prep_batch.values()[0])
        ]
