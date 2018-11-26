from reports.diagnostics.common.inspector_utils import read_explog, get_chip_type_from_exp_log, get_sequencer_kits, \
    format_kit_tag


def get_proton_tags(archive_path):
    tags = []

    chip_type = get_chip_type_from_exp_log(read_explog(archive_path))

    if chip_type:
        tags.append("{} Chip".format(chip_type))

    template_kit_name, inspector_seq_kit, system_type = get_sequencer_kits(archive_path)
    tags.append(format_kit_tag(template_kit_name))
    tags.append(format_kit_tag(inspector_seq_kit))

    return tags
