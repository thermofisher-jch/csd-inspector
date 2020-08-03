from reports.diagnostics.common.inspector_utils import get_xml_from_run_log, get_chip_names_from_element_tree, \
    get_kit_from_element_tree, format_kit_tag, get_lines_from_chef_gui_logs, get_parsed_loadcheck_data


def get_chef_tags(archive_path):
    tags = []

    chef_run_log = get_xml_from_run_log(archive_path)

    chip_a, chip_b = get_chip_names_from_element_tree(chef_run_log)
    if chip_a:
        tags.append("{} Chip".format(chip_a))

    if chip_b:
        tags.append("{} Chip".format(chip_b))

    kit = get_kit_from_element_tree(chef_run_log)
    tags.append(format_kit_tag(kit))

    chef_gui_log = get_lines_from_chef_gui_logs(archive_path)
    loadcheck_data = get_parsed_loadcheck_data(chef_gui_log)

    reagents_lot = loadcheck_data.get("chefReagentsLot", None)
    solutions_lot = loadcheck_data.get("chefSolutionsLot", None)
    if solutions_lot:
        tags.append("ChefSolutionLot: {}".format(solutions_lot))
    if reagents_lot:
        tags.append("ChefReagentLot: {}".format(reagents_lot))

    return tags
