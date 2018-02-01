#!/usr/bin/env python

import sys
import os.path
from datetime import datetime
from IonInspector.reports.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:

        # parse the file name for the starting time of the run
        xml_name = os.path.basename(os.path.splitext(get_chef_run_log_xml_path(archive_path))[0])
        xml_parts = xml_name.split('_')
        date_string = xml_parts[2] + "-" + xml_parts[3]
        run_start = datetime.strptime(date_string, '%Y-%m-%d-%H%M')

        # now get the xml root node to get the notifications
        root = get_xml_from_run_log(archive_path)
        notification_elements = root.findall("Warnings_Run/warning")

        notifications = list()
        for notification_element in notification_elements:
            # sometimes we get warning elements without children
            if len(notification_element.getchildren()) == 0:
                continue

            notification = {
                'time': '',
                'usr': '',
                'sys': '',
                'sys_name': '',
                'usr_msg': '',
                'resolution': '',
                'msg': '',
            }

            for node in notification_element.getiterator():
                notification[node.tag] = node.text

            # to compensate for an error in the chef software sometimes warnings are added which are prior to the run
            # so we are going to have to parse the time and compare the start time from the xml file name
            try:
                notification['time'] = datetime.strptime(notification['time'], '%Y%m%d_%H%M%S')
            except ValueError:
                pass

            if isinstance(notification['time'], datetime) and notification['time'] > run_start:
                notifications.append(notification)

        context = Context({"notifications": notifications})
        write_results_from_template(context, output_path)

        if notifications:
            return print_warning("There were notifications, please see results page.")
        else:
            return print_ok("There were no notifications in the chef log.")
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    execute(sys.argv[1], sys.argv[2], sys.argv[3])
