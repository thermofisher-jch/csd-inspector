from datetime import datetime

import functools32

from reports.diagnostics.common import inspector_utils
from reports.diagnostics.common.core_csa.types import IExpLogParser
from reports.diagnostics.common.inspector_utils import EXPLOG_DATETIME_FORMAT


class ExpLogParser(IExpLogParser):
    def __init__(self, archive_root_path, text_explog_path):
        IExpLogParser.__init__(self)
        self._archive_root_path = archive_root_path
        self._text_explog_path = text_explog_path
        with open(text_explog_path, "rb") as efh:
            self._explog_content = inspector_utils.read_explog_from_handle(efh)

    @functools32.lru_cache(maxsize=16)
    def get(self, attr_key, default=None):
        return self._explog_content.get(attr_key, default)

    @property
    @functools32.lru_cache(maxsize=1)
    def error_log(self):
        return self._explog_content.get("ExperimentErrorLog", "")

    @property
    @functools32.lru_cache(maxsize=1)
    def start_time(self):
        start_time = self._explog_content.get("Start Time", "")
        if start_time > "":
            start_time = datetime.strptime(start_time, EXPLOG_DATETIME_FORMAT)
        else:
            start_time = None
        return start_time

    @property
    @functools32.lru_cache(maxsize=1)
    def end_time(self):
        end_time = self._explog_content.get("End Time", "")
        if end_time > "":
            end_time = datetime.strptime(end_time, EXPLOG_DATETIME_FORMAT)
        else:
            end_time = None
        return end_time

    @property
    def explog_path(self):
        return self._text_explog_path
