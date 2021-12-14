def load_genexus():
    from reports.diagnostics.di.instrument_types.genexus import (
        GenexusInstrumentTypeContainer,
    )

    return GenexusInstrumentTypeContainer()


def load_purification():
    from reports.diagnostics.di.instrument_types.purification import (
        StandalonePurificationInstrumentTypeContainer,
    )

    return StandalonePurificationInstrumentTypeContainer()


INSTRUMENT_CONTAINERS = {
    u"Valkyrie": load_genexus,
    u"Purification": load_purification,
}


def get_instrument_type_container(archive_type_key):
    """
    In the 2.0 architecture, an 'entry_point' metadata registration under setup.py will
    be responsible for getting this dictionary built.

    Parameters
    ----------
    archive_type_key

    Returns
    -------
    An application-tier container for named instrument type key
    """
    # TODO: This should also be where the type-specific configuration is located and wired
    #       so that need not be repeated in every diagnostic entry method.
    return INSTRUMENT_CONTAINERS[archive_type_key]()
