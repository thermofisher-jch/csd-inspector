#!/usr/bin/env python

from IonInspector.reports.diagnostics.common.inspector_utils import (
    read_explog,
    shutil,
    os,
    print_info,
)


def execute(archive_path, output_path, archive_type):
    explog = read_explog(archive_path)
    run_type = explog.get("RunType", "Unknown")

    valkyrie_workflow_path = os.path.join(archive_path, "ValkyrieWorkflow") + "/"

    files = os.listdir(valkyrie_workflow_path)

    if "results.json" in files:
        files.remove("results.json")

    if "ValkyrieWorkflow_block.html" in files:
        files.remove("ValkyrieWorkflow_block.html")

    if os.path.exists(valkyrie_workflow_path + "ValkyrieWorkflow_block.html"):

        shutil.copy(
            valkyrie_workflow_path + "ValkyrieWorkflow_block.html",
            os.path.join(output_path, "results.html"),
        )
        for file in files:
            try:
                shutil.copy(
                    valkyrie_workflow_path + file, os.path.join(output_path, file)
                )
            except IOError:
                pass

    message = "Run Type: {}".format(run_type)
    return print_info(message)
