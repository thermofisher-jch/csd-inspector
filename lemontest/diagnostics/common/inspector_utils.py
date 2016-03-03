import os
import re
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


def get_xml_from_run_log(archive_path):
    """
    Reads the xml data from run logs
    :param archive_path: The path to the archive
    :return: The root xml element
    """
    for path, dirs, names in os.walk(archive_path):
        if "test_results" not in path:
            for name in names:
                if "logs.tar" not in name:
                    rel_dir = os.path.relpath(path, archive_path)
                    rel = os.path.join(rel_dir, name)
                    full = os.path.join(path, name)
                    if rel.startswith("var/log/IonChef/RunLog/") and rel.endswith(".xml"):
                        xml_path = full

    if not os.path.exists(xml_path):
        raise Exception("No chef run log xml file.")

    # groom the xml of known error conditions
    with open(xml_path, 'r') as xml_file:
        xml = xml_file.read()

    xml = re.sub('< *', '<', xml)
    xml = re.sub('</ *', '</', xml)
    xml = re.sub('> *', '>', xml)

    return ElementTree.fromstring(xml)
