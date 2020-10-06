import csv
import json
import os
import shutil
import tempfile
import tarfile
import traceback
import warnings
from glob import glob
from datetime import datetime
from xml.etree import ElementTree
from django.core.serializers.json import DjangoJSONEncoder

import semver
from bs4 import BeautifulSoup
from django.template import Context, Template

from reports.utils import PGM_RUN, PROTON, S5, VALK, UNKNOWN_PLATFORM

warnings.filterwarnings("ignore", category=DeprecationWarning)
MAX_MESSAGE_LENGTH = 1040
EXPLOG_FINAL = "explog_final.txt"
EXPLOG = "explog.txt"
ION_PARAMS = "ion_params_00.json"

NOT_SCANNED = "NOT_SCANNED"


def check_supported(explog):
    """
    this will go through the explog and look for invalid hardware
    :param explog:
    """

    chip_type = get_chip_type_from_exp_log(exp_log=explog)
    if chip_type in ["521"]:
        raise Exception(
            "The " + chip_type + " Chip has been blacklisted and cannot be evaulated."
        )


def get_explog_path(archive_path):
    """
    This method will find either the explog_final.txt or explog.txt
    :return:
    """
    paths = [
        os.path.join(archive_path, "CSA", EXPLOG_FINAL),
        os.path.join(archive_path, "CSA", EXPLOG),
        os.path.join(archive_path, EXPLOG_FINAL),
        os.path.join(archive_path, EXPLOG),
    ]

    for path in paths:
        if os.path.exists(path):
            return path

    raise Exception("explog_final.txt and explog.txt are missing.")


def get_ion_param_path(archive_path):
    """
    This method will find ION_PARAMS under CSA (genexus) or root dir
    :return:
    """
    paths = [
        os.path.join(archive_path, "CSA", ION_PARAMS),
        os.path.join(archive_path, ION_PARAMS),
    ]

    for path in paths:
        if os.path.exists(path):
            return path

    return None


def get_debug_path(archive_path):
    path = os.path.join(archive_path, "CSA", "debug")
    if os.path.exists(path):
        return path
    else:
        return None


def read_explog(archive_path):
    """
    This method will read and output a array of colon delimited key/value pairs from the explog_final.txt
    :param archive_path: the root directory of the archive
    :param archive_type:
    :return:
    """
    with open(get_explog_path(archive_path)) as explog_handle:
        return read_explog_from_handle(explog_handle)


def read_explog_from_handle(explog_handle):
    # parse the log file for all of the values in a colon delimited parameter
    data = dict()
    exp_error = False
    exp_error_log = []
    for line in explog_handle:
        # Trying extra hard to accommodate formatting issues in explog
        datum = line.split(":", 1)
        if len(datum) == 2:
            key, value = datum
            if "ExperimentErrorLog" in line:
                exp_error = True
                continue
            data[key.strip()] = value.strip()
        if exp_error:
            line = line.strip()
            if line != "" and "ExpLog_Done" not in line:
                exp_error_log.append(line)
            if "ExpLog_Done" in line:
                data["ExperimentErrorLog"] = exp_error_log
                exp_error = False
    return data


def read_base_caller_json(archive_path, archive_type):
    """
    This method will read and output a nested dict from parsing basecaller_results/BaseCaller.json
    :param archive_path: the root directory of the archive
    :return:
    """
    if archive_type == "Valkyrie":
        path = os.path.join(
            archive_path, "CSA", "outputs", "BaseCallingActor-00", "BaseCaller.json"
        )
    else:
        path = os.path.join(archive_path, "basecaller_results", "BaseCaller.json")
    if not os.path.exists(path):
        raise Exception("BaseCaller.json missing")
    with open(path) as fp:
        return json.load(fp)


def read_ionstats_basecaller_json(archive_path, archive_type):
    if archive_type == "Valkyrie":
        path = os.path.join(
            archive_path,
            "CSA",
            "outputs",
            "BaseCallingActor-00",
            "ionstats_basecaller.json",
        )
    else:
        path = os.path.join(
            archive_path, "basecaller_results", "ionstats_basecaller.json"
        )
    if not os.path.exists(path):
        raise Exception("ionstats_basecaller.json missing")
    with open(path) as fp:
        return json.load(fp)


def handle_exception(exc, output_path):
    """
    Prints out a NA message and
    :param exc: The exception which occured
    :param output_path: The output path:
    :return:
    """

    try:
        write_error_html(output_path)
        return print_failed(str(exc))
    except:
        pass


def write_error_html(output_path):
    """
    Write the results html for an errorful run
    :param output_path:
    """
    results_path = os.path.join(output_path, "results.html")
    if os.path.exists(results_path):
        os.remove(results_path)
    with open(results_path, "w") as results_path:
        results_path.write("<head></head><body>")
        results_path.write(
            "<strong>Error which occurred during test execution</strong>"
        )
        results_path.write('<p style="white-space: pre-wrap; word-wrap: break-word;">')
        traceback.print_exc(file=results_path)
        results_path.write("</p></body>")


def print_alert(message):
    """
    print an alert message
    :param message: The message to print
    """
    return "Alert", 40, message


def print_warning(message):
    return print_alert(message)


def print_info(message):
    """
    prints the info message
    :param message: The message to print
    """
    return "Info", 20, message


def print_ok(message):
    """
    prints the ok message
    :param message: The message to print
    """
    return "OK", 10, message


def print_na(message):
    """
    prints the na message
    :param message:
    """
    return "NA", 0, message


def print_failed(message):
    """
    prints the failed message
    :param message:
    """
    return "Failed", 0, message


def get_csv_from_run_log(archive_path):
    """
    Reads the csv data from run logs
    :param archive_path: The path to the archive
    :return: A dictionary of lists, keyed by column name
    """

    # get path to all of the logs and xml data
    csv_path = ""
    run_log_directory = os.path.join(archive_path, "var", "log", "IonChef", "RunLog")
    for run_log in os.listdir(run_log_directory):
        if run_log.endswith(".csv"):
            csv_path = os.path.join(run_log_directory, run_log)
            break

    if not os.path.exists(csv_path):
        raise Exception("No chef run log csv file.")

    # groom the xml of known error conditions
    run_log = dict()
    with open(csv_path, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=",")
        # create a dictionary of lists
        for header in csv_reader.fieldnames:
            run_log[header] = list()

        # populate the lists in the dictionary
        for row in csv_reader:
            for header in csv_reader.fieldnames:
                run_log[header].append(row[header])

    return run_log


def get_chef_run_log_xml_path(archive_path):
    # get path to all of the logs and xml data
    xml_path = ""
    run_log_directory = os.path.join(archive_path, "var", "log", "IonChef", "RunLog")
    for run_log in os.listdir(run_log_directory):
        if run_log.endswith(".xml"):
            xml_path = os.path.join(run_log_directory, run_log)
            break

    if not os.path.exists(xml_path):
        raise Exception("No chef run log xml file.")

    return xml_path


def get_xml_from_run_log(archive_path):
    """
    Reads the xml data from run logs
    :param archive_path: The path to the archive
    :return: The root xml element
    """

    def check_element_node(node):
        """Helper method which it will detect incorrect encoded elements"""

        # we are going to check if there is inner text and if that inner text starts wikth a less than sign
        if node.text is not None and len(node.text) > 0 and node.text[0] == "<":
            fake_root = ElementTree.fromstring("<fakeroot>" + node.text + "</fakeroot>")
            for fake_node in fake_root.getchildren():
                node.append(fake_node)
            node.text = None

        # recurse through all the elements
        for child in node.getchildren():
            check_element_node(child)

    # get path to all of the logs and xml data
    xml_path = get_chef_run_log_xml_path(archive_path)

    # remove spaces from xml tags. Bs4 will just throw them out and we need them for some tests
    xml_lines = []
    with open(xml_path, "r") as xml_file:
        for xml_line in xml_file:
            # Remove space after <
            while "< " in xml_line:
                xml_line = xml_line.replace("< ", "<")
            # Remove space after </
            while "</ " in xml_line:
                xml_line = xml_line.replace("</ ", "</")
            # Fix &lt; and &gt;
            while "&lt;" in xml_line:
                xml_line = xml_line.replace("&lt;", "<")
            while "&gt;" in xml_line:
                xml_line = xml_line.replace("&gt;", ">")
            xml_lines.append(xml_line)

    # Use bs4/lxml parser first to repair invalid xml
    soup = BeautifulSoup("\n".join(xml_lines), "xml")

    # Then parse the repaired xml using xml.etree
    root = ElementTree.fromstring(str(soup))

    # we are going to do a check here to see the known error where some xml elements have been encoded as plain text
    check_element_node(root)

    return root


def parse_log_lines(raw_log_lines):
    # [BC]-[INFO]:2018-08-08 15:53:22,400: parseLoadCheckdata: (chefSolutionsSerial) = (12346150)
    parsed = []
    for line in raw_log_lines:
        if line.startswith("[") and ":" in line:
            line_level, remaining = line.split(":", 1)
            line_date, remaining = (
                datetime.strptime(remaining[:19], "%Y-%m-%d %H:%M:%S"),
                remaining[23:],
            )
            line_message = remaining[1:]
            parsed.append([line_level.strip(), line_date, line_message.strip()])
    return parsed


def get_lines_from_chef_gui_logs(archive_path):
    """
    This method will concatenate all of lines from all of the gui log files for a chef data set
    :param archive_path: The root path of the archive
    :return: A list of parsed lines
    """

    lines = list()
    log_directory = os.path.join(archive_path, "var", "log", "IonChef", "ICS")
    for log in os.listdir(log_directory):
        if log.startswith("gui"):
            if log.endswith(".log"):
                with open(os.path.join(log_directory, log)) as log_file:
                    lines += [
                        line.strip() for line in log_file.readlines() if line.strip()
                    ]
            elif log.endswith(".tar"):
                with tarfile.open(os.path.join(log_directory, log)) as log_tar:
                    for log_name in log_tar.getmembers():
                        log_file = log_tar.extractfile(log_name)
                        lines += [
                            line.strip()
                            for line in log_file.readlines()
                            if line.strip()
                        ]
    return sorted(parse_log_lines(lines), key=lambda x: x[1])  # sort by date


def get_chip_type_from_exp_log(exp_log):
    """
    Gets the chip type from the exp log
    :parameter exp_log: Gets the exp log
    :return: A string of the exp log
    """
    if "ChipType" not in exp_log:
        raise Exception("Cannot find Chip Type")

    chip = exp_log["ChipType"]
    if chip == "900":
        # get the chip type
        if "ChipVersion" not in exp_log:
            raise Exception("Chip version missing from explog_final.txt")

        chip = exp_log["ChipVersion"].split(".")[0]

    chip_type = chip if len(chip) < 3 else chip[:3]
    return "PQ" if chip_type == "P2" else chip_type


def parse_ts_version(version_string):
    if version_string.count(".") < 2:
        version_string += ".0"
    if ".RC" in version_string:
        version_string = version_string.replace(".RC", "-rc.")
    if version_string.count(".") > 2 and "-" not in version_string:
        version_numbers = version_string.split(".")
        version_string = "{core_ver}-{pre_rel}".format(
            core_ver=".".join(version_numbers[0:3]),
            pre_rel=".".join(version_numbers[3:]),
        )

    semver.parse(version_string)  # Ensure that the string is not valid
    return version_string


def get_ts_version(archive_path):
    paths = [
        os.path.join(archive_path, "CSA", "version.txt"),
        os.path.join(archive_path, "version.txt"),
    ]

    for path in paths:
        if os.path.exists(path):
            break
    else:
        raise Exception("Could not find version.txt!")

    # get the version number
    with open(path) as f:
        line = f.readline()
        version = line.split("=")[-1].strip()
        version = version.split()[0]
        return parse_ts_version(version.strip())


def run_used_chef(archive_path):
    ion_params_path = os.path.join(archive_path, "ion_params_00.json")
    if not os.path.exists(ion_params_path):
        raise ValueError("Could not load ion_params_00.json.")
    with open(ion_params_path) as ion_params_file:
        ion_params_object = json.load(ion_params_file)
    return len(ion_params_object.get("exp_json", {}).get("chefInstrumentName", "")) > 0


def write_results_from_template(data_dict, output_dir, diagnostic_script_dir):
    template_path = os.path.join(diagnostic_script_dir, "results.html")
    try:
        template = Template(open(template_path).read())
        result = template.render(Context(data_dict))
        with open(os.path.join(output_dir, "results.html"), "w") as out:
            out.write(result.encode("UTF-8"))
    except IOError:
        raise Exception("Could not find template file at: " + template_path)

    with open(os.path.join(output_dir, "main.json"), "w") as fp:
        assert type(data_dict) in {list, dict}
        json.dump(data_dict, fp, cls=DjangoJSONEncoder)


class TemporaryDirectory(object):
    """Context manager for tempfile.mkdtemp() so it's usable with "with" statement."""

    def __init__(self, file_mappings):
        self.file_mappings = file_mappings

    def __enter__(self):
        self.name = tempfile.mkdtemp()
        for path, contents in self.file_mappings.iteritems():
            full_path = os.path.join(self.name, path.lstrip("/"))
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))
            with open(full_path, "w") as fp:
                fp.write(contents)
        return self.name

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self.name)


def parse_run_date_from_xml_path(path):
    """
    Parse run date from file paths like: "/opt/example/242470284-000327_rl_2017-4-18_1759.xml"
    """
    _, date_str, time_str = path.rsplit("_", 2)
    return datetime.strptime(date_str + "_" + time_str, "%Y-%m-%d_%H%M.xml")


def get_chip_names_from_element_tree(element_tree):
    """
    Extract chip name from a chef run log element tree. Two items of note:
    * There may be two chips <chip> and <chip2>
    * For proton chips, the <chip> element only contains the major version number. <chipVersion>
      contains the minor version. So P1v3 would be <chip>1</chip> <chipVersion>3</chipVersion>
    * Chip 500 is the chef balance chip
    """
    names = [None, None]
    for i, suffix in enumerate(["", "2"]):
        chip_element = element_tree.find("./RunInfo/chip" + suffix)
        chip_version_element = element_tree.find("./RunInfo/chipVersion" + suffix)
        if chip_element is not None:
            chip_element_text = chip_element.text.strip()
            if chip_element_text == "500":
                names[i] = "Balance"
            elif chip_element_text.isdigit() and int(chip_element_text) < 10:
                if chip_version_element is not None:
                    names[i] = (
                        "P"
                        + chip_element_text
                        + "v"
                        + chip_version_element.text.strip()
                    )
                else:
                    names[i] = "P" + chip_element_text
            else:
                names[i] = chip_element_text
    return names


def get_kit_from_element_tree(element_tree):
    kit_names = {
        "pgm_ic_v2": "Ion PGM Hi-Q Chef Kit",
        "pgm_ic_v1": "Ion PGM IC 200 Kit",
        "pi_ic_v1": "Ion PI IC 200 Kit",
        "pi_ic_v2": "Ion PI Hi-Q Chef Kit",
        "s530_1": "Ion 520/530 Kit-Chef",
        "s540_1": "Ion 540 Kit-Chef",
        "as_1": "Ion AmpliSeq Kit for Chef DL8",
        "pgm_ionchef_200_kit": "Ion PGM IC 200 Kit",
        "pi_ic200": "Ion PI IC 200 Kit",
        "pgm_3": "Ion PGM Hi-Q View Chef Kit",
        "hid_s530_1": "Ion Chef HID S530 V1",
        "hid_s530_2": "Ion Chef HID S530 V2",
        "hid_as_1": "Ion Chef HID Library V1",
        "hid_as_2": "Ion Chef HID Library V2",
        "s521_1": "Ion 520/530 ExT Kit-Chef V1",
    }

    kit_customer_facing_name_tag = element_tree.find("RunInfo/kit_customer_facing_name")
    kit_name_tag = element_tree.find("RunInfo/kit")

    name_tag = None
    if kit_customer_facing_name_tag is not None:
        name_tag = kit_customer_facing_name_tag
    else:
        name_tag = kit_name_tag

    if name_tag is not None:
        kit_name = name_tag.text.strip()
        return kit_names.get(kit_name, kit_name)
    else:
        return None


def format_reads(count):
    if count >= 1000000:
        return "{:,} million".format(round((count / 1000000.0), 1))
    else:
        return "{:,}".format(int(count))


def get_run_log_data(lines, fields=[]):
    # Read csv
    run_log_data = {"stages": [], "labels": [], "rows": []}

    csv_file = csv.DictReader(lines, delimiter=",", quotechar='"')
    current_stage = "START"
    current_stage_start_time = 0
    new_time = None
    # Get rows
    for row in csv_file:
        # Add data
        new_row = []
        for field, display_name, formatter in fields:
            if row.get(field) is None:
                new_row.append(None)
            else:
                new_row.append(formatter(row.get(field)))
        run_log_data["rows"].append(new_row)
        # Track the stage intervals
        new_time = float(row["timestamp"])
        new_stage = row["stage0"].upper() if row["stage1"] != "PAUSE" else "PAUSE"
        if current_stage != new_stage:
            run_log_data["stages"].append(
                {
                    "name": current_stage,
                    "start": current_stage_start_time,
                    "end": new_time,
                }
            )
            current_stage = new_stage
            current_stage_start_time = new_time
    # Add final stage
    if new_time is not None:
        run_log_data["stages"].append(
            {"name": current_stage, "start": current_stage_start_time, "end": new_time}
        )

    # Make labels
    run_log_data["labels"] = [display_name for field, display_name, formatter in fields]

    return run_log_data


def guard_against_unicode(kitName, kitType):
    try:
        kitName.decode("ascii")
    except UnicodeEncodeError:
        return kitName.encode("ascii", "ignore")
    except UnicodeDecodeError:
        return "Unknown %s" % kitType

    return kitName


def get_platform_and_systemtype(explog):
    platform = explog.get("Platform", UNKNOWN_PLATFORM)
    systemtype = explog.get("SystemType", "Unknown System Type")

    # PGM is special case
    if "PGM HW" in explog:
        return PGM_RUN, "PGM" + explog.get("PGM HW")

    # Proton is in lower case
    if platform == "proton":
        return PROTON, systemtype

    # system type for S5 will contain information such S5 Prime
    if platform == S5:
        return S5, systemtype

    # system type for Valkyrie is Dx
    if platform == VALK:
        return VALK, "Genexus"

    return platform, systemtype


def get_sequencer_kits(archive_path):
    # read the ion params file
    params_path = get_ion_param_path(archive_path)
    params = dict()
    if params_path:
        with open(params_path) as params_file:
            params = json.load(params_file)

    # read explog text files (explog_final.txt > explog.txt)
    exp_log = read_explog(archive_path)

    template_kit_name = (
        params.get("exp_json", {}).get("chefKitType", None)  # S5
        or params.get("exp_json", {}).get("chefReagentID", None)  # Genexus
        or params.get("plan", {}).get("templatingKitName", None)  # TS RUO
        or "Unknown Templating Kit"
    )
    template_kit_name = guard_against_unicode(template_kit_name, "Templating Kit")

    # get sequencing kit from exp_json (Genexus and S5)
    inspector_seq_kit = (
        exp_log.get("SeqKitDesc", None)  # Proton
        or exp_log.get("SeqKitPlanDesc", None)  # TS RUO
        or params.get("exp_json", {}).get("sequencekitname", None)  # S5 / Genexus
        or "Unknown Sequencing Kit"
    )
    inspector_seq_kit = guard_against_unicode(inspector_seq_kit, "Sequencing Kit")

    # get the system type
    _, system_type = get_platform_and_systemtype(exp_log)
    system_type = guard_against_unicode(system_type, "System Type")

    return template_kit_name, inspector_seq_kit, system_type


def read_ion_params(archive_path):
    # read the ion params file
    params_path = get_ion_param_path(archive_path)
    params = dict()
    if params_path:
        with open(params_path) as params_file:
            params = json.load(params_file)
    return params


def get_chip_lot_from_efuse(explog):
    efuse = parse_efuse(explog.get("Chip Efuse", ""))
    return efuse.get("L", "")


def get_s5_lot_info(archive_path):
    """S5"""

    def prep_info(info):
        info["productDesc"] = guard_against_unicode(
            info.get("productDesc", ""), ""
        ).strip()
        info["lotNumber"] = guard_against_unicode(info.get("lotNumber", ""), "").strip()
        return info

    # read explog text files (explog_final.txt > explog.txt)
    exp_log = read_explog(archive_path)
    chip_lot = get_chip_lot_from_efuse(exp_log)

    sequencing_lot_info, wash_lot_info, cleaning_lot_info = dict(), dict(), dict()
    try:
        products = dict()
        with open(get_init_log_path(archive_path), "r") as f:
            lines = f.readlines()
            products = parse_init_log(lines)

        for key, value in products.items():
            if "sequencing" in key.lower():
                sequencing_lot_info = prep_info(value)
            elif "wash" in key.lower():
                wash_lot_info = prep_info(value)
            elif "cleaning" in key.lower():
                cleaning_lot_info = prep_info(value)
    except OSError:
        # get_init_log_path raise OSError
        pass

    # chef reagents
    params = read_ion_params(archive_path)
    chef_solution_lot, chef_reagent_lot = "", ""
    if "exp_json" in params:
        chef_solution_lot = params["exp_json"].get("chefSolutionsLot", "")
        chef_reagent_lot = params["exp_json"].get("chefReagentsLot", "")

    return {
        "chefSolutionsLot": guard_against_unicode(chef_solution_lot, "").strip(),
        "chefReagentsLot": guard_against_unicode(chef_reagent_lot, "").strip(),
        "chipLot": chip_lot,
        "sequencingLotInfo": sequencing_lot_info,
        "washLotInfo": wash_lot_info,
        "cleaningLotInfo": cleaning_lot_info,
    }


def get_kit_lot_info(archive_path):
    """PGM, Proton, Chef"""

    # read explog text files (explog_final.txt > explog.txt)
    exp_log = read_explog(archive_path)
    chip_lot = get_chip_lot_from_efuse(exp_log)

    # PGM only
    sequencer_lot = exp_log.get("SeqKitLot", "")
    if sequencer_lot == NOT_SCANNED:
        sequencer_lot = ""

    # chef reagents
    params = read_ion_params(archive_path)
    chef_solution_lot, chef_reagent_lot = "", ""
    if "exp_json" in params:
        chef_solution_lot = params["exp_json"].get("chefSolutionsLot", "")
        chef_reagent_lot = params["exp_json"].get("chefReagentsLot", "")

    chef_solution_lot = guard_against_unicode(chef_solution_lot, "").strip()
    chef_reagent_lot = guard_against_unicode(chef_reagent_lot, "").strip()
    sequencer_lot = guard_against_unicode(sequencer_lot, "").strip()

    return chef_solution_lot, chef_reagent_lot, sequencer_lot, chip_lot


def format_kit_tag(tag):
    if not tag:
        return "Unknown Chef Kit"
    tag = tag.replace("Ion", "")
    tag = tag.replace("Reagents", "")
    tag = tag.replace("AmpliSeq Kit for", "")
    tag = tag.replace("  ", " ")
    return tag.strip()


def parse_experimentinfo_line(line):
    key = ""
    data = {}
    for item in line.split():
        if "=" in item:
            key, value = item.split("=")
            data[key] = [value]
        else:
            data[key].append(item)
    return data


def read_flow_info_from_explog(explog):
    keys = [k for k in explog.keys() if k.startswith("acq") and k.endswith(".dat")]
    keys = sorted(keys)
    flow_data = {}
    for i, k in enumerate(keys):
        flow_data[i] = parse_experimentinfo_line(explog[k])
        flow_data[i]["dat_name"] = k

    return flow_data


def parse_efuse(value):
    ASSEMBLY = {"D": "Tong Hsing", "C": "Corwill"}

    # any character other than 'X' will be 'RUO'
    # For example, it will start with 'A' and then toggling over to 'B'
    PRODUCT = {"X": "Dx"}

    values = {}

    # if empty or None, return empty dict
    if not value:
        return values

    # raw values
    for chunk in value.split(","):
        if ":" in chunk:
            k, v = chunk.split(":", 1)
            values[k] = v

    # extra values
    values["Assembly"] = ASSEMBLY.get(values["BC"][2], "Unknown Assembly")
    values["Product"] = PRODUCT.get(values["BC"][3], "RUO")

    values["ExpirationYear"] = ord(values["BC"][4]) - ord("A") + 2015
    values["ExpirationMonth"] = ord(values["BC"][5]) - ord("A") + 1

    return values


def get_parsed_loadcheck_data(lines):
    loadcheck_key = "parseLoadCheckdata"
    data = {}
    for line in lines:
        if loadcheck_key not in line[2]:
            continue

        loadcheck = (
            line[2].split(":").pop().replace("(", "").replace(")", "").replace(" ", "")
        )
        k, v = loadcheck.split("=")
        data[k] = v

    return data


def get_genexus_kit_info(archive_path):
    deck_status = os.path.join(archive_path, "CSA", "DeckStatus.json")
    planned_run = os.path.join(archive_path, "CSA", "planned_run.json")

    deck_info = {}
    if os.path.exists(deck_status):
        with open(deck_status, "r") as f:
            deck_info = json.load(f)

    deck_kit_lot_mapping = {}
    for kit in deck_info:
        ktype = kit["kitType"]
        barcodes = kit["barcodeList"]
        if not ktype in deck_kit_lot_mapping:
            deck_kit_lot_mapping[ktype] = {}

        for barcode in barcodes:
            part_number = (
                barcode["partNumber"] if barcode.get("partNumber", None) else "na"
            )
            lot_number = barcode.get("lotNumber", "")
            deck_kit_lot_mapping[ktype][part_number] = lot_number

    kit_config = {}
    if os.path.exists(planned_run):
        with open(planned_run, "r") as f:
            data = json.load(f)
            kit_config = data.get("object", {}).get("kitConfig", {})

    kit_config_mapping = {}
    for config in kit_config:
        ktype = config["kitType"]
        components = config["components"] if config["components"] else []

        if not ktype in kit_config_mapping:
            kit_config_mapping[ktype] = {}

        for component in components:
            ctype = component["kitType"]
            name = component.get("externalKitName", "")
            part_number = component.get("kitPartNumber", "")
            kit_config_mapping[ktype][ctype] = {}
            kit_config_mapping[ktype][ctype]["name"] = name
            kit_config_mapping[ktype][ctype]["partNumber"] = part_number

    return deck_kit_lot_mapping, kit_config_mapping


def get_genexus_lot_number(deck_kit_lot_mapping, kit_config_mapping, kit_types={}):
    if not kit_types:
        kit_types = {
            "LibraryKit": ["Solution", "Reagent"],
            "TemplatingKit": ["Solution", "Reagent"],
            "SequencingKit": ["Solution", "Reagent"],
            "ChipKit": ["Chip"],
        }

    for ktype, components in kit_types.items():
        if ktype not in deck_kit_lot_mapping:
            continue

        if ktype not in kit_config_mapping:
            continue

        for ctype in components:
            if ctype not in kit_config_mapping[ktype]:
                continue

            part_number = kit_config_mapping[ktype][ctype]["partNumber"]
            name = kit_config_mapping[ktype][ctype]["name"]

            lot_number = deck_kit_lot_mapping[ktype].get(part_number, "")
            if part_number not in deck_kit_lot_mapping[ktype]:
                lot_number = deck_kit_lot_mapping[ktype].get("na")

            if lot_number:
                yield "GX{k}{c}: {l}".format(
                    l=lot_number,
                    k=ktype.replace("Kit", "")
                    .replace("Library", "Lib")
                    .replace("Templating", "Tpl")
                    .replace("Sequencing", "Seq"),
                    c=ctype.replace("Chip", "")
                    .replace("Solution", "Sln")
                    .replace("Reagent", "Rgt"),
                )


def get_init_log_path(archive_path):
    init_paths = [
        os.path.join(archive_path, "CSA", "InitLog.txt"),
        os.path.join(archive_path, "InitLog.txt"),
    ]

    for p in init_paths:
        if os.path.exists(p):
            return p

    raise OSError("InitLog.txt is not found")


def parse_init_log(log_lines):
    date_formats = {"expDate": "%Y/%m/%d"}
    product_dict = {}
    current_product = None
    for line in log_lines:
        if line.startswith("productDesc: "):
            # start of block we want to parse
            current_product = line.split(":", 1)[1].strip()
            product_dict[current_product] = {"productDesc": current_product}
        elif line.startswith("remainingUses: "):
            # end of block we want to parse
            product_dict[current_product]["remainingUses"] = line.split(":", 1)[
                1
            ].strip()
            current_product = None
        elif current_product:
            # in block we want to parse
            key, value = line.split(":", 1)
            if key in date_formats:
                try:
                    product_dict[current_product][key] = datetime.strptime(
                        value.strip(), date_formats[key]
                    ).date()
                except ValueError:
                    product_dict[current_product][key] = value.strip()
            else:
                product_dict[current_product][key] = value.strip()
    return product_dict

# Parse the search dir and get file path (can be used to find bead density, bfmask.stats, etc)
def get_filePath(archive_path, fileName=None, searchDir="CSA/outputs/SigProcActor-00/"):
    if fileName:
        availableFilePaths = [y for x in os.walk(os.path.join(
            archive_path, searchDir)) for y in glob(os.path.join(x[0], fileName))]
        for filePath in availableFilePaths:
            if os.path.isfile(filePath):
                return filePath

    return None
