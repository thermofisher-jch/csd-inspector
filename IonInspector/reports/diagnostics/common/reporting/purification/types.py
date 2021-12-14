import abc


class IPathLocator(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def debug_log(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def lib_prep_run_log(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def quant_summary_log(self):
        raise NotImplementedError()


class IFeatureAvailability(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def extraction_release_version(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def has_quant_summary_consumables_section(self):
        raise NotImplementedError()
