import os
import logging
from reports.diagnostics.common.inspector_utils import (
    read_explog,
    get_chip_type_from_exp_log,
    get_sequencer_kits,
    format_kit_tag,
    get_ts_version,
    parse_ts_version,
    get_genexus_kit_info,
    get_genexus_lot_number,
    get_serial_no,
)

logger = logging.getLogger(__name__)

def get_valk_tags(archive_path):
    tags = []

    chip_type = get_chip_type_from_exp_log(read_explog(archive_path))
    if chip_type and chip_type != "---":
        tags.append("{} Chip".format(chip_type))
        
    integrated_run=False
    csa_path=os.path.join(archive_path,"CSA")
    for dirname, dirnames, filenames in os.walk(csa_path):
        for subdirname in dirnames:
            dirpath=os.path.join(csa_path,subdirname)
            for dirname2, dirnames2, filenames2 in os.walk(dirpath):
                for filename in filenames2:
                    #logger.warn("checking "+dirpath+"/" + filename)
                    if filename == "Quant_summary.csv":
                        integrated_run=True
                        logger.warn("found "+dirpath+"/Quant_summary.csv")

    if not integrated_run:
        logger.warn("did not find Quant_summary.csv")
        
        
    template_kit_name, inspector_seq_kit, system_type = get_sequencer_kits(archive_path)
    if template_kit_name:
        tags.append(format_kit_tag(template_kit_name))
    if inspector_seq_kit:
        tags.append(format_kit_tag(inspector_seq_kit))
    if integrated_run:
        tags.append("Genexus_Integrated")

    kit_types = {
        "LibraryKit": ["Solution", "Reagent"],
        "TemplatingKit": ["Solution", "Reagent"],
        "SequencingKit": ["Solution", "Reagent"],
        "ChipKit": ["Chip"],
    }

    deck_kit_lot_mapping, kit_config_mapping = get_genexus_kit_info(archive_path)
    tags.extend(
        list(
            get_genexus_lot_number(deck_kit_lot_mapping, kit_config_mapping, kit_types)
        )
    )

    version = get_ts_version(archive_path)
    if version:
        tags.append("TS " + parse_ts_version(version))

    tags.append(get_serial_no(archive_path))

    return tags
