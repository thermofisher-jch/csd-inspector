import csv
import json
import os
import shutil
import tempfile
import traceback
import warnings
from datetime import datetime
from xml.etree import ElementTree

import semver
from bs4 import BeautifulSoup
from django.template import Context, Template

warnings.filterwarnings("ignore", category=DeprecationWarning)
MAX_MESSAGE_LENGTH = 1040
EXPLOG_FINAL = "explog_final.txt"
EXPLOG = "explog.txt"


def check_supported(explog):
    """
    this will go through the explog and look for invalid hardware
    :param explog:
    """

    chip_type = get_chip_type_from_exp_log(exp_log=explog)
    if chip_type in ['521']:
        raise Exception("The " + chip_type + " Chip has been blacklisted and cannot be evaulated.")


def get_explog_path(archive_path):
    """
    This method will find either the explog_final.txt or explog.txt
    :return:
    """
    path = os.path.join(archive_path, EXPLOG_FINAL)
    if os.path.exists(path):
        return path

    path = os.path.join(archive_path, EXPLOG)
    if os.path.exists(path):
        return path

    raise Exception("explog_final.txt and explog.txt are missing.")


def read_explog(archive_path):
    """
    This method will read and output a array of colon delimited key/value pairs from the explog_final.txt
    :param archive_path: the root directory of the archive
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


def read_base_caller_json(archive_path):
    """
    This method will read and output a nested dict from parsing basecaller_results/BaseCaller.json
    :param archive_path: the root directory of the archive
    :return:
    """
    path = os.path.join(archive_path, "basecaller_results", "BaseCaller.json")
    if not os.path.exists(path):
        raise Exception("BaseCaller.json missing")
    with open(path) as fp:
        return json.load(fp)


def read_ionstats_basecaller_json(archive_path):
    path = os.path.join(archive_path, "basecaller_results", "ionstats_basecaller.json")
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
    with open(results_path, 'w') as results_path:
        results_path.write('<head></head><body>')
        results_path.write('<strong>Error which occurred during test execution</strong>')
        results_path.write('<p style="white-space: pre-wrap; word-wrap: break-word;">')
        traceback.print_exc(file=results_path)
        results_path.write('</p></body>')


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
    run_log_directory = os.path.join(archive_path, 'var', 'log', 'IonChef', 'RunLog')
    for run_log in os.listdir(run_log_directory):
        if run_log.endswith('.csv'):
            csv_path = os.path.join(run_log_directory, run_log)
            break

    if not os.path.exists(csv_path):
        raise Exception("No chef run log csv file.")

    # groom the xml of known error conditions
    run_log = dict()
    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
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
    run_log_directory = os.path.join(archive_path, 'var', 'log', 'IonChef', 'RunLog')
    for run_log in os.listdir(run_log_directory):
        if run_log.endswith('.xml'):
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
    with open(xml_path, 'r') as xml_file:
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


def get_lines_from_chef_gui_logs(archive_path):
    """
    This method will concatenate all of lines from all of the gui log files for a chef data set
    :param archive_path: The root path of the archive
    :return: A list of strings for each line
    """

    gui_lines = list()
    gui_log_directory = os.path.join(archive_path, 'var', 'log', 'IonChef', 'ICS')
    for gui_log in os.listdir(gui_log_directory):
        if gui_log.startswith('gui') and gui_log.endswith('.log'):
            with open(os.path.join(gui_log_directory, gui_log)) as gui_log_file:
                gui_lines += gui_log_file.readlines()
    return gui_lines


def get_chip_type_from_exp_log(exp_log):
    """
    Gets the chip type from the exp log
    :parameter exp_log: Gets the exp log
    :return: A string of the exp log
    """
    if 'ChipType' not in exp_log:
        raise Exception("Cannot find Chip Type")

    chip = exp_log['ChipType']
    if chip == '900':
        # get the chip type
        if 'ChipVersion' not in exp_log:
            raise Exception("Chip version missing from explog_final.txt")

        chip = exp_log['ChipVersion'].split(".")[0]

    chip_type = chip if len(chip) < 3 else chip[:3]
    return 'PQ' if chip_type == 'P2' else chip_type


def parse_ts_version(version_string):
    if version_string.count(".") < 2:
        version_string += ".0"
    if ".RC" in version_string:
        version_string = version_string.replace(".RC", "-rc.")
    semver.parse(version_string)  # Ensure that the string is not valid
    return version_string


def get_ts_version(archive_path):
    version_path = os.path.join(archive_path, "version.txt")
    if not os.path.exists(version_path):
        raise Exception("Missing file: " + version_path)

    # get the version number
    line = open(version_path).readline()
    version = line.split('=')[-1].strip()
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
        with open(os.path.join(output_dir, "results.html"), 'w') as out:
            out.write(result.encode("UTF-8"))
    except IOError:
        raise Exception('Could not find template file at: ' + template_path)


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
                    names[i] = "P" + chip_element_text + "v" + chip_version_element.text.strip()
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
