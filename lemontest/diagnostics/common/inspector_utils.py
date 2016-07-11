import csv
import os
import re
import traceback
from xml.etree import ElementTree


def read_explog(archive_path):
    """
    This method will read and output a array of colon delimited key/value pairs from the explog_final.txt
    :param archive_path: the root directory of the archive
    :return:
    """
    path = os.path.join(archive_path, "explog_final.txt")
    if not os.path.exists(path):
        raise Exception("explog_final.txt missing")

    # parse the log file for all of the values in a colon delimited parameter
    data = {}
    for line in open(path):
        # Trying extra hard to accommodate formatting issues in explog
        datum = line.split(":", 1)
        if len(datum) == 2:
            key, value = datum
            data[key.strip()] = value.strip()

    return data


def handle_exception(exc, output_path):
    """
    Prints out a NA message and
    :param exc: The exception which occured
    :param output_path: The output path:
    :return:
    """
    print_na(str(exc))
    results_path = os.path.join(output_path, "results.html")
    if os.path.exists(results_path):
        os.remove(results_path)
    with open(results_path, 'w') as results_path:
        traceback.print_exc(file=results_path)


def print_alert(message):
    """
    print an alert message
    :param message: The message to print
    """
    print("Alert")
    print(40)
    print(message)


def print_warning(message):
    """
    prints the warning message
    :param message: The message to print
    """
    print("Warning")
    print(30)
    print(message)


def print_info(message):
    """
    prints the info message
    :param message: The message to print
    """
    print("Info")
    print(20)
    print(message)


def print_ok(message):
    """
    prints the ok message
    :param message: The message to print
    """
    print("OK")
    print(10)
    print(message)


def print_na(message):
    """
    prints the na message
    :param message:
    """
    print("N/A")
    print(0)
    print(message)


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


def get_xml_from_run_log(archive_path):
    """
    Reads the xml data from run logs
    :param archive_path: The path to the archive
    :return: The root xml element
    """

    # get path to all of the logs and xml data
    xml_path = ""
    run_log_directory = os.path.join(archive_path, 'var', 'log', 'IonChef', 'RunLog')
    for run_log in os.listdir(run_log_directory):
        if run_log.endswith('.xml'):
            xml_path = os.path.join(run_log_directory, run_log)
            break

    if not os.path.exists(xml_path):
        raise Exception("No chef run log xml file.")

    # groom the xml of known error conditions
    with open(xml_path, 'r') as xml_file:
        xml = xml_file.read()

    xml = re.sub('< *', '<', xml)
    xml = re.sub('</ *', '</', xml)
    xml = re.sub('> *', '>', xml)

    return ElementTree.fromstring(xml)


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

    return chip if len(chip) < 3 else chip[:3]
