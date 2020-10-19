from reports.diagnostics.common.inspector_utils import (
    read_explog,
    get_chip_type_from_exp_log,
    get_sequencer_kits,
    format_kit_tag,
    get_ts_version,
    parse_ts_version,
    get_kit_lot_info,
    get_serial_no
)


def get_proton_tags(archive_path):
    tags = []

    chip_type = get_chip_type_from_exp_log(read_explog(archive_path))
    if chip_type:
        tags.append("{} Chip".format(chip_type))

    template_kit_name, inspector_seq_kit, system_type = get_sequencer_kits(archive_path)
    if template_kit_name:
        tags.append(format_kit_tag(template_kit_name))
    if inspector_seq_kit:
        tags.append(format_kit_tag(inspector_seq_kit))

    chef_solution_lot, chef_reagent_lot, sequencer_lot, chip_lot = get_kit_lot_info(archive_path)
    if chef_solution_lot:
        tags.append("ChefSln: {}".format(chef_solution_lot))
    if chef_reagent_lot:
        tags.append("ChefRgt: {}".format(chef_reagent_lot))
    if sequencer_lot:
        tags.append("ProtonSeqRgt: {}".format(sequencer_lot))
    if chip_lot:
        tags.append("ProtonChip: {}".format(chip_lot))

    version = get_ts_version(archive_path)
    if version:
        tags.append("TS " + parse_ts_version(version))
    
    tags.append(get_serial_no(archive_path))

    return tags
