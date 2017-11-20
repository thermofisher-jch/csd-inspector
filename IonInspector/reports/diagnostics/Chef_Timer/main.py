#!/usr/bin/env python

from datetime import datetime, timedelta
import gzip
import sys
import os
from IonInspector.reports.diagnostics.common.inspector_utils import *


def seconds_to_hours_minutes(total_seconds):
    m, s = divmod(total_seconds, 60)
    h, m = divmod(m, 60)
    return h, m


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


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        # the amount of time mr coffee was requested to pause for
        mrcoffee_pause_time_seconds = 0
        mrcoffee_line_date_time = None

        # the boolean flag for a manual pause time request
        user_pause_request = False
        user_pause_request_date_time = None

        # the start date time for the manual pause
        user_pause_start = None

        # the end date time for the manual pause
        user_pause_end = None

        # total time that the chef process ran (don't bother parsing, just keep it as a string)
        total_time = ''
        total_time_date_time = None

        # get a dictionary key'ed off of the log names and get all of the information
        run_log_csv = get_csv_from_run_log(archive_path)
        for file_name, is_log in get_instrument_server_logs(archive_path).iteritems():
            date_string = file_name.split('-', 1)[1].split('.')[0].rsplit('-', 2)[0]
            for is_line in is_log:
                try:
                    time_string = is_line.split(' ', 1)[0].strip()
                    line_date_time = datetime.strptime(date_string + " " + time_string, '%Y-%m-%d %H:%M:%S.%f')
                except:
                    continue

                if 'process: PAUSE' in is_line:
                    if not user_pause_start or line_date_time > user_pause_start:
                        user_pause_start = line_date_time

                if 'process: UNPAUSE' in is_line:
                    if not user_pause_end or line_date_time > user_pause_end:
                        user_pause_end = line_date_time

                if 'timing: Run Scheduler mrcoffee' in is_line:
                    if not mrcoffee_line_date_time or line_date_time > mrcoffee_line_date_time:
                        mrcoffee_pause_time_seconds = int(is_line.replace(" seconds.", "").split(" ")[-1])

                if 'process: user_pause' in is_line:
                    if not user_pause_request_date_time or line_date_time > user_pause_request_date_time:
                        user_pause_request_date_time = line_date_time
                        user_pause_request = is_line.split(':')[-1].strip().lower() in ['true', 't', '1']

                if 'timing: ' in is_line:
                    if not total_time_date_time or line_date_time > total_time_date_time:
                        total_time_date_time = line_date_time
                        total_time = is_line.split(':', 4)[-1].strip()

        # Change formatting on total_time
        h_string, m_string, s_string = total_time.split(":")
        total_time_string = h_string + " " + m_string

        manual_pause = "No Manual Pause"
        if user_pause_start and user_pause_end:
            manual_pause = "User Pause Option: %ih %im" % seconds_to_hours_minutes(
                (user_pause_end - user_pause_start).seconds
            )

        mrcoffee_pause_time_sting = "Mr Coffee Pause: %ih %im" % seconds_to_hours_minutes(mrcoffee_pause_time_seconds)

        summary = "Total Time: " + total_time_string + " - "
        summary += manual_pause if user_pause_request else mrcoffee_pause_time_sting
        return print_info(summary)
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)