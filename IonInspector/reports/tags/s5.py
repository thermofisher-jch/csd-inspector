from reports.diagnostics.common.inspector_utils import read_explog, get_chip_type_from_exp_log


def get_s5_tags(archive_path):
    tags = []

    chip_type = get_chip_type_from_exp_log(read_explog(archive_path))

    if chip_type:
        tags.append("{} Chip".format(chip_type))

    return tags
