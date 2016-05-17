#!/usr/bin/env python

from datetime import datetime
import gzip
import sys
import os
import traceback
from lemontest.diagnostics.common.inspector_utils import *


def get_instrument_server_logs(archive_path):
    """
    This method will concat all of the log files in the IS directory for chef
    :param archive_path: The path to the archive
    :return: A list of the lines of the log
    """

    lines = dict()
    instrument_server_directory = os.path.join(archive_path, 'var', 'log', 'IonChef', 'IS')
    # get all of the uncompressed log files
    for log_file in [s for s in os.listdir(instrument_server_directory) if s.endswith('.log')]:
        with open(os.path.join(instrument_server_directory, log_file), 'r') as log_handle:
            lines[log_file] = log_handle.readlines()

    # get all of the compressed log files
    for compressed_log_file in [s for s in os.listdir(instrument_server_directory) if s.endswith('.log.gz')]:
        with gzip.open(os.path.join(instrument_server_directory, compressed_log_file), 'r') as log_handle:
            lines[compressed_log_file] = log_handle.readlines()

    return lines

try:
    archive, output = sys.argv[1:3]

    # extract the "mrcoffee" element from the run log
    root = get_xml_from_run_log(archive)
    name_tag = root.find("RunInfo/mrcoffee")
    if name_tag is None:
        raise Exception("Failed to find mrcoffee xml element.")

    # parse the total time into the summary
    total_minutes = int(name_tag.text)
    hours = int(total_minutes / 60)
    minutes = total_minutes % 60
    summary = "No delay." if total_minutes == 0 else "Timer Option Used: "
    if hours:
        summary += "{} Hours ".format(hours)
    if minutes:
        summary += "{} Minutes".format(minutes)

    # get any pause times in the log
    pause_time = None
    unpause_time = None
    for file_name, is_log in get_instrument_server_logs(archive).iteritems():
        date_string = file_name.split('-', 1)[1].split('.')[0].rsplit('-', 2)[0]
        for is_line in is_log:

            if 'process: PAUSE' in is_line:
                time_string = is_line.split(' ', 1)[0].strip()
                pause_time = datetime.strptime(date_string + " " + time_string, '%Y-%m-%d %H:%M:%S.%f')
                print pause_time

            if 'process: UNPAUSE' in is_line:
                time_string = is_line.split(' ', 1)[0].strip()
                unpause_time = datetime.strptime(date_string + " " + time_string, '%Y-%m-%d %H:%M:%S.%f')
                break

    if pause_time and unpause_time:
        paused_length = unpause_time - pause_time
        summary += " | Paused: {}".format(paused_length)

    print_info(summary)
except Exception as exc:
    print_na(str(exc))

traceback.print_exc()