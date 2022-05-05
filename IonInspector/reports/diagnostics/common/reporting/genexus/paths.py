import logging
import os

import functools32
import semver

from reports.diagnostics.common.inspector_errors import FileNotFoundError
from reports.diagnostics.common.reporting.genexus import (
    IPathLocator,
    IFeatureAvailability,
)
from reports.diagnostics.common.reporting.genexus.types import PurificationBatchSubdir

LOGGER = logging.getLogger("RenderReportRunner")


class GenexusArchiveFeatures(IPathLocator, IFeatureAvailability):
    def __init__(self, archive_root, explog, explog_provider, debug_log_provider):
        self._archive_root = archive_root
        self._explog = explog
        self._explog_provider = explog_provider
        self._debug_log_provider = debug_log_provider

    @property
    @functools32.lru_cache(maxsize=1)
    def csa_subdir(self):
        csa_subdir = os.path.join(self._archive_root, "CSA")
        if not os.path.isdir(csa_subdir):
            raise FileNotFoundError(csa_subdir)
        return csa_subdir

    @property
    @functools32.lru_cache(maxsize=1)
    def debug_log(self):
        retval = os.path.join(self.csa_subdir, "debug.log")
        if not os.path.isfile(retval):
            raise FileNotFoundError(retval)

    @property
    @functools32.lru_cache(maxsize=1)
    def purification_deck_log(self):
        """
        Returns
        -------
        None if this CSA pre-dates integrated purification mode, the path of
        PurificationRunDeck.json if it is sufficiently recent, or a FileNotFoundException
        if it is recent enough but the file is not found.
        """
        retval = None
        if self.has_standalone_purification:
            retval = os.path.join(self.csa_subdir, "PurificationDeckLog.json")
            if not os.path.isfile(retval):
                raise FileNotFoundError(retval)
        return retval

    @property
    @functools32.lru_cache(maxsize=1)
    def purification_run_logs(self):
        if not self.has_integrated_purification:
            return ()
        return (
            {
                batch_meta.batch_label: os.path.join(
                    batch_meta.subdir_path, "libPrep_log.csv"
                )
            }
            for batch_meta in self.purification_batch_metadata
        )

    @property
    @functools32.lru_cache(maxsize=1)
    def purification_quant_summaries(self):
        if not self.has_integrated_purification:
            return ()
        return (
            {
                batch_meta.batch_label: os.path.join(
                    batch_meta.subdir_path, "Quant_summary.csv"
                )
            }
            for batch_meta in self.purification_batch_metadata
        )

    @property
    @functools32.lru_cache(maxsize=1)
    def purification_batch_subdirs(self):
        if not self.has_integrated_purification:
            return ()
        batches = self.purification_batch_metadata
        return (batch_metadata.subdir_path for batch_metadata in batches)

    def _validate_batch_explog_candidate(self, explog_path):
        if not os.path.isfile(explog_path):
            return None
        batch_subdir = os.path.dirname(explog_path)
        try:
            explog = self._explog_provider(self._archive_root, explog_path)
            if explog.get("Extraction instrument Release_version") is None:
                return None
            debug_log_path = os.path.join(batch_subdir, "debug")
            debug_log = self._debug_log_provider(explog, debug_log_path)
            run_name = explog.get("runName")
            plan_name = explog.get("planName")
            batch_label = run_name[: len(run_name) - len(plan_name) - 1]
            return PurificationBatchSubdir(batch_label, batch_subdir, explog, debug_log)
        except Exception:
            LOGGER.exception("Unable to write ")
            return None

    @property
    @functools32.lru_cache(maxsize=1)
    def purification_batch_metadata(self):
        if not self.has_integrated_purification:
            return ()
        csa_subdir = self.csa_subdir
        return (
            batch_metadata
            for batch_metadata in (
                self._validate_batch_explog_candidate(
                    os.path.join(csa_subdir, child_path, "explog_final.txt")
                )
                for child_path in os.listdir(csa_subdir)
            )
            if batch_metadata is not None
        )
        # explogs = (
        #     explog for explog in (
        #         self._explog_provider(self._archive_root, explog_path)
        #         for explog_path in candidate_explogs
        #     ) if explog.get("Extraction instrument Release_version") is not None
        # )
        # return (
        #     {
        #         "explog": log_and_dir["explog"],
        #         "debug_log": self._debug_log_provider(
        #             log_and_dir["explog"],
        #             os.path.join(log_and_dir["batch"], "debug")
        #         ),
        #         "batch": log_and_dir["batch"],
        #         "label": log_and_dir["explog"].get("ExperimentName", log_and_dir["batch"])
        #     }
        #     for log_and_dir in (
        #         {
        #             "explog": self._explog_provider(
        #                 self._archive_root,
        #                 os.path.join(batch_subdir, "explog_final.txt")
        #             ),
        #             "batch": batch_subdir
        #         }
        #         for batch_subdir in self.purification_batch_subdirs
        #     )
        # )

    @property
    @functools32.lru_cache(maxsize=1)
    def genexus_release(self):
        version_str = self._explog.get("Genexus Release_version", "")
        if version_str != "":
            versions=version_str.split(".")
            rc = {}
            if len(versions) >= 1:
                rc["major"]=int(versions[0])
            if len(versions) >= 2:
                rc["minor"]=int(versions[1])
            return rc

    @property
    @functools32.lru_cache(maxsize=1)
    def has_standalone_purification(self):
        version = self.genexus_release
        return version["major"] >= 6 and version["minor"] >= 4

    @property
    @functools32.lru_cache(maxsize=1)
    def has_integrated_purification(self):
        version = self.genexus_release
        return version["major"] >= 6 and version["minor"] >= 6

    @property
    @functools32.lru_cache(maxsize=1)
    def has_quant_summary_consumables_section(self):
        version = self.genexus_release
        return version["major"] >= 6 and version["minor"] >= 5
