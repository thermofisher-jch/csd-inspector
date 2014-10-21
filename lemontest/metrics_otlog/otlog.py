__author__ = 'Anthony Rodriguez'

import sys
import csv
import os
from decimal import Decimal

'''
    Task: parse otlog metrics
    @author: Anthony Rodriguez
'''
class OTLog(object):

    '''
        Task: init variables, calls validate_path function
        @param    archive_path:    path to the otlog
        @param    logger:          system logger to log errors
    '''
    def __init__(self, archive_path, logger):
        self.archive_path= archive_path
        self.logger = logger
        self.file_path, self.valid = self.validate_path(archive_path)

    '''
        Task: check to see if given path was valid
        @return    True:    valid
        @return    False:   not valid
    '''
    def is_valid(self):
        return self.valid

    '''
        Task: validates existence of otlog path
        @param    archive_path:    path to the otlog
        @return   '', False:       onetouch.log does not exist
        @return   path, True:      full path to onetouch.log if it exists
    '''
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, 'onetouch.log')
        if not os.path.exists(path):
            self.logger.warning('onetouch.log does not exist')
            return '', False
        else:
            return path, True

    '''
        Task: validates existence of otlog path
        @return    ot_version:    one touch version
        @return    None:          not found
    '''
    def get_ot_version(self):
        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                first_row = csv_reader.next()

                ot_version = first_row[2].split(':')[1].strip()
            except:
                print sys.exc_info()[0]
                ot_version = None

            if ot_version:
                return unicode(ot_version)
            else:
                return None

    '''
        Task: gets highest recorded ambient temperature
        @return    max_temp:    highest recorded Thermistor-0 Temperature
        @return    None:        no max found
    '''
    def get_ambient_temp_high(self):
        max_temp = float('-inf')

        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    max_temp = max(max_temp, Decimal(row[1]))
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        if max_temp != float('-inf'):
            max_temp = Decimal(max_temp)
            return max_temp
        else:
            return None

    '''
        Task: gets lowest recorded ambient temperature
        @return    min_temp:    lowest recorded Thermistor-0 Temperature
        @return    None:        no min found
    '''
    def get_ambient_temp_low(self):
        min_temp = float('inf')

        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    min_temp = min(min_temp, Decimal(row[1]))
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        if min_temp != float('inf'):
            min_temp = Decimal(min_temp)
            return min_temp
        else:
            return None

    '''
        Task: gets highest recorded case temperature
        @return    max_temp:    highest recorded Thermistor-3 Temperature
        @return    None:        no max found
    '''
    def get_internal_case_temp_high(self):
        max_temp = float('-inf')

        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    max_temp = max(max_temp, Decimal(row[4]))
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        if  max_temp != float('-inf'):
            max_temp = Decimal(max_temp)
            return max_temp
        else:
            return None

    '''
        Task: gets lowest recorded case temperature
        @return    min_temp:    lowest recorded Thermistor-3 Temperature
        @return    None:        no min found
    '''
    def get_internal_case_temp_low(self):
        min_temp = float('inf')

        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    min_temp = min(min_temp, Decimal(row[4]))
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        if min_temp != float('inf'):
            min_temp = Decimal(min_temp)
            return min_temp
        else:
            return None

    '''
        Task: gets highest recorded pressure
        @return    max_press:   highest recorded P_SensorCur.Pressure
        @return    None:        no max found
    '''
    def get_pressure_high(self):
        max_press = float('-inf')

        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    max_press = max(max_press, Decimal(row[6]))
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        if max_press != float('-inf'):
            max_press = Decimal(max_press)
            return max_press
        else:
            return None

    '''
        Task: gets lowest recorded pressure
        @return    min_press:   lowest recorded P_SensorCur.Pressure
        @return    None:        no min found
    '''
    def get_pressure_low(self):
        min_press = float('inf')

        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    min_press = min(min_press, Decimal(row[6]))
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        if min_press != float('inf'):
            min_press = Decimal(min_press)
            return min_press
        else:
            return None

    '''
        Task: checks if machine aborted within first hour
        @return    'Yes':       < 3600 lines of data recorded
        @return    'No':        >= 3600 lines of data recorded
        @return    None:        <= 2 lines of data found
    '''
    def get_sample_inject_abort(self):
        number_of_rows = 0
        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)
            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()
                for row in csv_reader:
                    number_of_rows += 1
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        if number_of_rows:
            if number_of_rows < 3600:
                return u'Yes'
            else:
                return u'No'
        else:
            return None

    '''
        Task: gets total runtime
        @return    runtime:    total number of lines recorded; one per second
    '''
    def get_run_time(self):
        number_of_rows = 0

        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    number_of_rows += 1
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        run_time = number_of_rows

        return run_time

    '''
        Task: checks if error code 5 occurred in oil pump during operation
        @return    u'5':    error code 5 was found
        @return    None:    error code 5 NOT found
    '''
    def get_oil_pump_status(self):
        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    if int(row[24]) == 5:
                        return unicode(5)
            except:
                print sys.exc_info()[0]

        return None

    '''
        Task: checks if error code 5 occurred in sample pump during operation
        @return    u'5':    error code 5 was found
        @return    None:    error code 5 NOT found
    '''
    def get_sample_pump_status(self):
        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    if int(row[25]) == 5:
                        return unicode(5)
            except:
                print sys.exc_info()[0]

        return None