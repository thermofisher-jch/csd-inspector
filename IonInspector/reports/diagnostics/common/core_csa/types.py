import abc
from collections import namedtuple


class IExpLogParser(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get(self, attr_key, default=None):
        raise NotImplementedError()

    @abc.abstractproperty
    def error_log(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def start_time(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def end_time(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def explog_path(self):
        raise NotImplementedError()

    # @abc.abstractmethod
    # def get_chip_type(self):
    #     raise NotImplementedError()


class IDebugLogParser(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def error_log(self):
        raise NotImplementedError()


DebugErrors = namedtuple("DebugErrors", ["before", "during", "after", "has_errors"])


class BatchErrorsModel(object):
    def __init__(self, batch_label, experiment_errors, debug_errors):
        self._batch_label = batch_label
        self._experiment_errors = [error for error in experiment_errors]
        self._debug_errors = DebugErrors(
            (error for error in debug_errors.before),
            (error for error in debug_errors.during),
            (error for error in debug_errors.after),
            debug_errors.has_errors,
        )

    @property
    def batch_label(self):
        return self._batch_label

    @property
    def experiment_errors(self):
        return [error for error in self._experiment_errors]

    @property
    def before_debug_errors(self):
        return [error for error in self._debug_errors.before]

    @property
    def during_debug_errors(self):
        return [error for error in self._debug_errors.during]

    @property
    def after_debug_errors(self):
        return [error for error in self._debug_errors.after]

    @property
    def has_debug_errors(self):
        return self._debug_errors.has_errors or len(self._experiment_errors) > 0
