import abc


class IPathLocator(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def csa_subdir(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def debug_log(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def purification_deck_log(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def purification_batch_metadata(self):
        """
        If the current archive is a 6.5 or later run, then it can be checked for integrated mode
        purification runs, each of which has a label, explog, and debug log that this property
        will gather and return.  Other purification mode parsers, like the quant summary and
        run log parsers, are not returned in this style.  The explog and debug log parsers
        are because it is necessary to create the explog parser in order to look up the
        batch label used to refer to each distinct batch, so we have already created these
        artifacts to answer a more fundamental requirement and so may as well return them and
        capture the invested effort.

        Returns
        -------
        A dictionary with four keys.  "debug_log" and "explog" give the log handling services,
        "batch" returns the directory root for the batch, and "label" returns a display-worthy
        label representing each batch run instance.
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def purification_batch_subdirs(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def purification_run_logs(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def purification_quant_summaries(self):
        raise NotImplementedError()


class IFeatureAvailability(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def genexus_release(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def has_standalone_purification(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def has_integrated_purification(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def has_quant_summary_consumables_section(self):
        raise NotImplementedError()


class PurificationBatchSubdir(object):
    def __init__(self, batch_label, subdir_path, explog_parser, debug_log_parser):
        self._batch_label = batch_label
        self._subdir_path = subdir_path
        self._explog_parser = explog_parser
        self._debug_log_parser = debug_log_parser

    @property
    def batch_label(self):
        return self._batch_label

    @property
    def subdir_path(self):
        return self._subdir_path

    @property
    def explog_parser(self):
        return self._explog_parser

    @property
    def debug_log_parser(self):
        return self._debug_log_parser
