import csv
import os
import re
import json
import traceback
from django.template import Context, Template
from xml.etree import ElementTree
from bs4 import BeautifulSoup

MAX_MESSAGE_LENGTH = 140


def check_supported(explog):
    """
    this will go through the explog and look for invalid hardware
    :param explog:
    """

    chip_type = get_chip_type_from_exp_log(exp_log=explog)
    if chip_type in ['521']:
        raise Exception("The " + chip_type + " Chip has been blacklisted and cannot be evaulated.")


def read_explog(archive_path):
    """
    This method will read and output a array of colon delimited key/value pairs from the explog_final.txt
    :param archive_path: the root directory of the archive
    :return:
    """
    path = os.path.join(archive_path, "explog_final.txt")
    if not os.path.exists(path):
        path = os.path.join(archive_path, "explog.txt")
    if not os.path.exists(path):
        raise Exception("explog_final.txt and explog.txt are missing.")

    return read_explog_from_handle(open(path))


def read_explog_from_handle(explog_handle):
    # parse the log file for all of the values in a colon delimited parameter
    data = dict()
    expError = False
    expErrorLog = []
    for line in explog_handle:
        # Trying extra hard to accommodate formatting issues in explog
        datum = line.split(":", 1)
        if len(datum) == 2:
            key, value = datum
            if "ExperimentErrorLog" in line:
                expError = True
                continue
            data[key.strip()] = value.strip()
        if expError:
            line = line.strip()
            if line != "" and "ExpLog_Done" not in line:
                expErrorLog.append(line)
            if "ExpLog_Done" in line:
                data["ExperimentErrorLog"] = expErrorLog
                expError = False
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
    with open(path) as base_caller_fh:
        base_caller_json = json.load(base_caller_fh)
    return base_caller_json


def handle_exception(exc, output_path):
    """
    Prints out a NA message and
    :param exc: The exception which occured
    :param output_path: The output path:
    :return:
    """

    try:
        print_failed(str(exc))
        write_error_html(output_path)
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
    print("Alert")
    print(40)
    print(message[:MAX_MESSAGE_LENGTH])


def print_warning(message):
    """
    prints the warning message
    :param message: The message to print
    """
    print("Warning")
    print(30)
    print(message[:MAX_MESSAGE_LENGTH])


def print_info(message):
    """
    prints the info message
    :param message: The message to print
    """
    print("Info")
    print(20)
    print(message[:MAX_MESSAGE_LENGTH])


def print_ok(message):
    """
    prints the ok message
    :param message: The message to print
    """
    print("OK")
    print(10)
    print(message[:MAX_MESSAGE_LENGTH])


def print_na(message):
    """
    prints the na message
    :param message:
    """
    print("NA")
    print(0)
    print(message[:MAX_MESSAGE_LENGTH])


def print_failed(message):
    """
    prints the failed message
    :param message:
    """
    print("Failed")
    print(0)
    print(message[:MAX_MESSAGE_LENGTH])


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

    # get path to all of the logs and xml data
    xml_path = get_chef_run_log_xml_path(archive_path)

    # Use bs4/lxml parser first to repair invalid xml
    with open(xml_path, 'r') as xml_file:
        soup = BeautifulSoup(xml_file, "xml")

    # Then parse the repaired xml using xml.etree
    return ElementTree.fromstring(str(soup))


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


def get_ts_version(archive_path):
    version_path = os.path.join(archive_path, "version.txt")
    if not os.path.exists(version_path):
        raise Exception("Missing file: " + version_path)

    # get the version number
    line = open(version_path).readline()
    version = line.split('=')[-1].strip()
    version = version.split()[0]
    return version.strip()


def write_results_from_template(data_dict, output_dir):
    template = Template(open("results.html").read())
    result = template.render(Context(data_dict))
    with open(os.path.join(output_dir, "results.html"), 'w') as out:
        out.write(result.encode("UTF-8"))