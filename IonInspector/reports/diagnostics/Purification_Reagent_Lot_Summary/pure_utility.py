import os.path

from reports.diagnostics.common.inspector_errors import (
    FileNotFoundError,
    FilesNotFoundError,
)
from reports.diagnostics.common.quantum_data_source import (
    QuantFeatureEvaluator,
    QuantDataSource,
)


def find_purification_files(archive_path, required=set()):
    files = {
        "libPrep_log": os.path.join(archive_path, "libPrep_log.csv"),
        "Quant_summary": os.path.join(archive_path, "Quant_summary.csv"),
        "Report_detailed": os.path.join(archive_path, "Report_detailed.json"),
        "debug": os.path.join(archive_path, "debug"),
    }
    present = set()
    for key, path in files.items():
        if os.path.isfile(path):
            present.add(key)
    errors = list()
    for key in required:
        if not key in present:
            errors.append(files[key])
    if not len(errors) == 0:
        if len(errors) == 1:
            raise FileNotFoundError(errors[0])
        else:
            raise FilesNotFoundError(errors)
    files["present"] = present
    return files
