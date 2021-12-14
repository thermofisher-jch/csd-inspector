#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from reports.diagnostics.common.inspector_utils import (
    print_info,
    get_sequencer_kits,
)


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    template_kit_name, inspector_seq_kit, system_type = get_sequencer_kits(archive_path)
    return print_info(" | ".join([system_type, inspector_seq_kit, template_kit_name]))


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
