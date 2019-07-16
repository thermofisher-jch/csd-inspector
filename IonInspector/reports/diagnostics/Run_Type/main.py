#!/usr/bin/env python

from IonInspector.reports.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    explog = read_explog(archive_path)
    run_type = explog.get("RunType", "Unknown")

    valkyrie_workflow_path = os.path.join(archive_path, "ValkyrieWorkflow") + "/"

    files = [
        "workflow_timing.png",
        "VacuumLog.html",
        "TubeBottomLog.csv",
        "flow_spark.svg"
    ]

    if os.path.exists(valkyrie_workflow_path + "ValkyrieWorkflow_block.html"):

        shutil.copy(valkyrie_workflow_path + "ValkyrieWorkflow_block.html",
                    os.path.join(output_path, "results.html"))
        for file in files:
            try:
                shutil.copy(valkyrie_workflow_path + file, os.path.join(output_path, file))
            except IOError:
                pass

    message = "Run Type: {}".format(run_type)
    return print_info(message)
