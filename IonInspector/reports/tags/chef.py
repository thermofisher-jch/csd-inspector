from reports.diagnostics.common.inspector_utils import get_xml_from_run_log, get_chip_names_from_element_tree, \
    get_kit_from_element_tree


def get_chef_tags(archive_path):
    tags = []

    chef_run_log = get_xml_from_run_log(archive_path)

    chip_a, chip_b = get_chip_names_from_element_tree(chef_run_log)
    if chip_a:
        tags.append("{} Chip".format(chip_a))

    if chip_b:
        tags.append("{} Chip".format(chip_b))

    kit = get_kit_from_element_tree(chef_run_log)
    if "ampli" in kit.lower():
        tags.append("AmpliSeq")

    return tags
