# -*- coding: utf-8 -*-
# !/usr/bin/env python
import os.path
import sys

from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    write_results_from_template,
)
from IonInspector.reports.diagnostics.common.quantum_data_source import (
    inject_quant_data_source,
)
from IonInspector.reports.diagnostics.Purification_Quant_Summary.pure_utility import (
    find_purification_files,
)


def execute(archive_path, output_path, _archive_type):
    files_config = find_purification_files(archive_path)
    quant_source = inject_quant_data_source(files_config)
    write_results_from_template(
        {
            "header_data": quant_source.quant_header_record.to_html(
                bold_rows=True,
                classes="header-table table table-bordered table-sm",
                header=False,
                columns=["value"],
                justify="left",
                col_space=400,
                index_names=False,
            ),
            "quant_data": quant_source.quant_samples_table.to_html(
                justify="center",
                bold_rows=False,
                header=True,
                index=False,
                classes="quant-table card-body table table-bordered table-striped",
                columns=[
                    "Sample Plate  Well",
                    "Well Name",
                    "Archive Plate Well",
                    "Creation Date",
                    "Type",
                    "Concentration",
                ],
            ),
        },
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    return print_info("See results for details.")


if __name__ == "__main__":
    archive_path_arg, output_path_arg, archive_type_arg = sys.argv[1:4]
    execute(archive_path_arg, output_path_arg, archive_type_arg)
