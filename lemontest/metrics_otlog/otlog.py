import datetime
import sys
import csv
import os
from decimal import Decimal

class OTLog(object):

    def __init__(self, archive_path, logger):
        self.archive_path= archive_path
        self.logger = logger
        self.file_path, self.valid = self.validate_path(archive_path)

    def is_valid(self):
        return self.valid

    def validate_path(self, archive_path):
        path = os.path.join(archive_path, 'onetouch.log')
        if not os.path.exists(path):
            self.logger.warning('onetouch.log does not exist')
            return '', False
        else:
            return path, True

    # One Touch version
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

    # Thermistor-0 Temperature
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

    # Thermistor-0 Temperature
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

    # Thermistor-3 Temperature
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

    # Thermistor-3 Temperature
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

    # P_SensorCur.Pressure
    def get_pressure_high(self):
        max_temp = float('-inf')

        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    max_temp = max(max_temp, Decimal(row[6]))
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        if max_temp != float('-inf'):
            max_temp = Decimal(max_temp)
            return max_temp
        else:
            return None

    # P_SensorCur.Pressure
    def get_pressure_low(self):
        min_temp = float('inf')

        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                for row in csv_reader:
                    min_temp = min(min_temp, Decimal(row[6]))
            except:
                '''occurs if file has less than two lines'''
                print sys.exc_info()[0]

        if min_temp != float('inf'):
            min_temp = Decimal(min_temp)
            return min_temp
        else:
            return None

    # if # of rows < 3600: No; else: Yes
    def get_sample_inject_abort(self):
        with open(self.file_path, 'r') as log_file:
            csv_reader = csv.reader(log_file)

            try:
                # Ignore first two lines
                first_line = csv_reader.next()
                second_line = csv_reader.next()

                number_of_rows = 0

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

    # # of rows / 3600
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

        #run_time = unicode(datetime.timedelta(seconds=number_of_rows))
        run_time = number_of_rows

        return run_time

    # Print error code if present
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

    # Print error code if present
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