#!/usr/bin/env python

import sys
from IonInspector.reports.diagnostics.common.inspector_utils import *
from plots.nuc_step import get_nuc_step_dygraphs_data
from plots.key_trace import get_key_traces_dygraphs_data


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    key_trace_regions = []
    for region in ["inlet", "middle", "outlet"]:
        with open(
            archive_path + "/sigproc_results/NucStep/NucStep_" + region + "_bead.txt"
        ) as bead_fp:
            with open(
                archive_path
                + "/sigproc_results/NucStep/NucStep_"
                + region
                + "_empty.txt"
            ) as empty_fp:
                key_trace_regions.append(
                    [region.title(), bead_fp.readlines(), empty_fp.readlines()]
                )

    with open(
        archive_path + "/sigproc_results/NucStep/NucStep_frametime.txt"
    ) as time_fp:
        frame_times = [float(i) for i in time_fp.read().strip().split()]

    context = {
        "nuc_step": json.dumps(get_nuc_step_dygraphs_data(archive_path)),
        "key_trace": json.dumps(
            get_key_traces_dygraphs_data(key_trace_regions, frame_times)
        ),
    }

    write_results_from_template(
        context, output_path, os.path.dirname(os.path.realpath(__file__))
    )

    return print_info("WIP replacement for Raw Trace. See results for details.")


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
