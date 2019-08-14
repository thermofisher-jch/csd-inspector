#!/usr/bin/env python
import os
import json
from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    write_results_from_template,
)


def execute(archive_path, output_path, archive_type):
    with open(os.path.join(archive_path, "CSA/planned_run.json")) as fp:
        deck_configs = json.load(fp)["object"]["deckConfig"]
    write_results_from_template(
        {"deck_configs": deck_configs},
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    return print_info("See results for details.")
