from reports.diagnostics.common.inspector_utils import (
    read_explog,
    get_chip_type_from_exp_log,
    get_sequencer_kits,
    format_kit_tag,
    get_ts_version,
    parse_ts_version,
    get_s5_lot_info,
    get_serial_no,
)


def genereate_lot_info_tags(lot_info, key_name, tag_name):
    if lot_info.get(key_name, None) and lot_info[key_name]["productDesc"]:
        if lot_info[key_name]["lotNumber"] == "Not Found":
            return ""

        ext = "ExT" if "ExT" in lot_info[key_name]["productDesc"] else ""
        return "S5{ext}{tag_name}: {lot}".format(
            ext=ext, lot=lot_info[key_name]["lotNumber"], tag_name=tag_name
        )

    return ""


def get_s5_tags(archive_path):
    tags = []

    chip_type = get_chip_type_from_exp_log(read_explog(archive_path))
    if chip_type:
        tags.append("{} Chip".format(chip_type))

    template_kit_name, inspector_seq_kit, system_type = get_sequencer_kits(archive_path)
    if template_kit_name:
        tags.append(format_kit_tag(template_kit_name))
    if inspector_seq_kit:
        tags.append(format_kit_tag(inspector_seq_kit))

    lot_info = get_s5_lot_info(archive_path)

    # chef ktis
    if lot_info.get("chefSolutionsLot"):
        tags.append("ChefSln: {}".format(lot_info.get("chefSolutionsLot")))

    if lot_info.get("chefReagentsLot"):
        tags.append("ChefRgt: {}".format(lot_info.get("chefReagentsLot")))

    if lot_info.get("chipLot"):
        tags.append("S5Chip: {}".format(lot_info.get("chipLot")))

    # sequencing kits
    kit_pairs = [
        ("sequencingLotInfo", "SeqRgt"),
        ("washLotInfo", "WashSln"),
        ("cleaningLotInfo", "CleanSln"),
    ]
    for key_name, tag_name in kit_pairs:
        tag = genereate_lot_info_tags(lot_info, key_name, tag_name)
        if tag:
            tags.append(tag)

    version = get_ts_version(archive_path)
    if version:
        tags.append("TS " + parse_ts_version(version))

    tags.append(get_serial_no(archive_path))

    return tags
