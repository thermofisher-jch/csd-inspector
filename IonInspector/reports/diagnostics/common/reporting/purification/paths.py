import os

import functools32
import semver

from reports.diagnostics.common.reporting.purification.types import (
    IPathLocator,
    IFeatureAvailability,
)


class StandaloneArchiveFeatures(IPathLocator, IFeatureAvailability):
    def __init__(self, archive_root, explog_parser):
        self._archive_root = archive_root
        self._explog_parser = explog_parser

    @property
    @functools32.lru_cache(maxsize=1)
    def debug_log(self):
        return os.path.join(self._archive_root, "debug.log")

    @property
    @functools32.lru_cache(maxsize=1)
    def lib_prep_run_log(self):
        return os.path.join(self._archive_root, "libPrep_log.csv")

    @property
    @functools32.lru_cache(maxsize=1)
    def quant_summary_log(self):
        return os.path.join(self._archive_root, "Quant_summary.csv")

    @property
    @functools32.lru_cache(maxsize=1)
    def extraction_release_version(self):
        version_str = self._explog_parser.get("Extraction Release_version", "")
        if version_str != "":
            return semver.parse(version_str)

    @property
    @functools32.lru_cache(maxsize=1)
    def has_quant_summary_consumables_section(self):
        version = self.extraction_release
        return version["major"] >= 6 and version["minor"] >= 5
