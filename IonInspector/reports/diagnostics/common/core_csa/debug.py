import itertools
import re

import functools32

from reports.diagnostics.Experiment_Errors.main import DEBUG_ERROR_KEYWORDS
from reports.diagnostics.common.core_csa import IDebugLogParser, DebugErrors
from reports.diagnostics.common import inspector_utils


ERROR_PATTERN = re.compile("|".join(DEBUG_ERROR_KEYWORDS))


class DebugLogParser(IDebugLogParser):
    def __init__(self, explog_parser, debug_log_path):
        self._explog_parser = explog_parser
        self._debug_log_path = debug_log_path

    @property
    @functools32.lru_cache(maxsize=1)
    def error_log(self):
        retval = {"before": [], "during": [], "after": []}
        if self._debug_log_path:
            with open(self._debug_log_path) as dh:
                start_time = self._explog_parser.start_time
                end_time = self._explog_parser.end_time

                def during_before_or_after(line):
                    out_datetime = inspector_utils.get_debug_log_datetime(
                        line=line, start=start_time
                    )
                    if start_time > out_datetime:
                        return "before"
                    if end_time and end_time < out_datetime:
                        return "after"
                    return "during"

                def during_or_before(line):
                    out_datetime = inspector_utils.get_debug_log_datetime(
                        line=line, start=start_time
                    )
                    return "before" if start_time > out_datetime else "during"

                src_iter = (line for line in dh if ERROR_PATTERN.search(line))
                if start_time:
                    if end_time:
                        for group_entry in itertools.groupby(
                            src_iter, during_before_or_after
                        ):
                            retval[group_entry[0]].extend(group_entry[1])
                    else:
                        for group_entry in itertools.groupby(
                            src_iter, during_or_before
                        ):
                            retval[group_entry[0]].extend(group_entry[1])
                else:
                    retval["during"].extend(src_iter)
        has_errors = (
            len(retval["before"]) + len(retval["during"]) + len(retval["after"])
        ) > 0
        return DebugErrors(
            retval["before"], retval["during"], retval["after"], has_errors
        )
