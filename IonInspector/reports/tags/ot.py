import os
from reports.diagnostics.common.inspector_utils import get_serial_no


def get_ot_tags(archive_path):
    tags = []

    with open(os.path.join(archive_path, "onetouch.log")) as log:
        script_line = log.readline()
    script = os.path.basename(script_line.split(",")[0])
    script_tag = script.replace(".txt", "")
    script_tag = script_tag.replace("_", " ")
    script_tag = "OT " + script_tag

    tags.append(script_tag)

    # One Touch does not have explog, so instead of finding a serial number this just adds a search tag
    # with the error message stating that no explog.txt file has been found.
    # tags.append(get_serial_no(archive_path))

    return tags
