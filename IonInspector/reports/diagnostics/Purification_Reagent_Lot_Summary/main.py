# -*- coding: utf-8 -*-
# !/usr/bin/env python
from dependency_injector import providers

from reports.diagnostics.common.inspector_utils import print_info
from reports.diagnostics.common.reporting import PURIFICATION_LOT_SUMMARY


def execute(archive_path, output_path, archive_type):
    from reports.diagnostics.di.instrument_types import get_instrument_type_container

    # TOOO: Apply configurable properties while loading container instead of
    #       repeating it in each test
    instrument_container = get_instrument_type_container(archive_type)
    instrument_container.config.purification.gap_tolerance.from_value(30)
    instrument_container.config.csa_core.archive_root.from_value(archive_path)
    instrument_container.config.csa_core.output_directory.from_value(output_path)
    instrument_container.config.csa_core.selected_report_name.from_value(
        PURIFICATION_LOT_SUMMARY
    )
    return instrument_container.process_report()


if __name__ == "__main__":
    import os
    import sys
    from django import setup

    os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
    setup()
    archive_path_arg, output_path_arg, archive_type_arg = sys.argv[1:4]
    execute(archive_path_arg, output_path_arg, archive_type_arg)
