'''
Author: Anthony Rodriguez
'''
import os
from decimal import Decimal
from datetime import datetime
from __builtin__ import ValueError

class Metrics_PGM_Explog(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.explog_data, self.explog_valid = self.validate_explog_path(archive_path)
        self.version_data, self.version_valid = self.validate_version_path(archive_path)

    # validate path existence
    def validate_explog_path(self, archive_path):
        path = os.path.join(archive_path, "explog_final.txt")
        if not os.path.exists(path):
            self.logger.warning("explog_final.txt not found")
            return "", False
        else:
            return self.open_explog(path), True

    # validate path existence
    def validate_version_path(self, archive_path):
        path = os.path.join(self.archive_path, "version.txt")
        if not os.path.exists(path):
            self.logger.warning("version.txt missing from archive")
            return "", False
        else:
            return self.open_version(path), True

    # open corresponding file
    def open_explog(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split(": ", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data

    # open corresponding file
    def open_version(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split("=", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data

    # return True if archive path is valid, and contains explog_final.txt
    # return False otherwise
    def is_explog_valid(self):
        return self.explog_valid

    # return True if archive path is valid, and contains version.txt
    # return False otherwise
    def is_version_valid(self):
        return self.version_valid

    # return PGM Temperature as a decimal
    # or log error message and return Null value
    def get_pgm_temperature(self):
        if "PGMTemperature" not in self.explog_data or not self.explog_data['PGMTemperature'].strip():
            self.logger.warning("PGM Temperature not in explog_data")
            return None
        else:
            temperature = Decimal(self.explog_data["PGMTemperature"].strip().split(" - ")[1])

            return temperature

    # return PGM Pressure as a decimal
    # or log error message and return Null value
    def get_pgm_pressure(self):
        if "PGMPressure" not in self.explog_data or not self.explog_data['PGMPressure'].strip():
            self.logger.warning("PGM Pressure not in explog_data")
            return None
        else:
            pressure = Decimal(self.explog_data["PGMPressure"].strip().split(" - ")[1])

            return pressure

    # return Chip Temperature as a decimal
    # or log error message and return Null value
    def get_chip_temperature(self):
        if "ChipTemperature" not in self.explog_data or not self.explog_data['ChipTemperature'].strip():
            self.logger.warning("Chip Temperature not in explog_data")
            return None
        else:
            temperature = Decimal(self.explog_data["ChipTemperature"].strip().split(" - ")[1])

            return temperature

    # return Chip Noise as a decimal
    # or log error message and return Null value
    def get_chip_noise(self):
        if "Noise_90pct" not in self.explog_data or not self.explog_data['Noise_90pct'].strip():
            self.logger.warning("Noise_90pct not in explog_data")
            return None
        else:
            noise = Decimal(self.explog_data["Noise_90pct"])

            return noise

    # return gain
    def get_gain(self):
        if "Gain" not in self.explog_data or not self.explog_data['Gain'].strip():
            self.logger.warning("Gain not it explog_data")
            return None
        else:
            chip_gain = Decimal(self.explog_data["Gain"])

            return chip_gain

    # return Run Type
    def get_cycles(self):
        if "Cycles" not in self.explog_data or not self.explog_data['Cycles'].strip():
            self.logger.warning("Cycles not in explog_data")
            return None
        else:
            run_type = unicode(self.explog_data["Cycles"].strip())

            return run_type

    # return Run Type
    def get_flows(self):
        if "Flows" not in self.explog_data or not self.explog_data['Flows'].strip():
            self.logger.warning("Flows not in explog_data")
            return None
        else:
            run_type = unicode(self.explog_data["Flows"].strip())

            return run_type

    # return chip type
    def get_chip_type(self):
        if "ChipType" not in self.explog_data or not self.explog_data['ChipType'].strip():
            self.logger.warning("Chip Type not in explog_data")
            return None
        else:
            chip_type = unicode(self.explog_data["ChipType"].strip())

            return chip_type

    # return Run Type
    def get_run_type(self):
        if "RunType" not in self.explog_data or not self.explog_data['RunType'].strip():
            self.logger.warning("Run Type not in explog_data")
            return None
        else:
            run_type = unicode(self.explog_data["RunType"].strip())

            return run_type

    # return reference library
    def get_reference(self):
        if 'Library' not in self.explog_data or not self.explog_data['Library'].strip():
            self.logger.warning("Reference Library Info not in explog_data")
            return None
        else:
            reference = unicode(self.explog_data['Library'].strip())
            if reference == 'none':
                return None

            return reference

    # return sequencing kit information
    def get_seq_kit(self):
        if "SeqKitDesc" not in self.explog_data or not self.explog_data['SeqKitDesc'].strip():
            if "SeqKitPlanDesc" not in self.explog_data or not self.explog_data['SeqKitPlanDesc'].strip():
                self.logger.warning("Sequencing Kit information missing from explog")
                return None
            else:
                seq_kit = unicode(self.explog_data["SeqKitPlanDesc"].strip())

                return seq_kit

        else:
            seq_kit = unicode(self.explog_data["SeqKitDesc"].strip())

            return seq_kit

    # return Seq Kit Lot
    def get_seq_kit_lot(self):
        if "SeqKitLot" not in self.explog_data or not self.explog_data['SeqKitLot'].strip():
            self.logger.warning("Seq Kit Lot not in explog_data")
            return None
        else:
            seq_kit_lot = unicode(self.explog_data['SeqKitLot'].strip())

            return seq_kit_lot

    # return hardware version
    def get_hw_version(self):
        if "PGM HW" not in self.explog_data or not self.explog_data['PGM HW'].strip():
            self.logger.warning("PGM HW not in explog_data")
            return None
        else:
            pgm_hw = unicode(self.explog_data['PGM HW'].strip())

            return pgm_hw

    # return software Version
    def get_sw_version(self):
        if "PGM SW Release" not in self.explog_data or not self.explog_data['PGM SW Release'].strip():
            self.logger.warning("Software Version not in explog_data")
            return None
        else:
            sw_version = unicode(self.explog_data['PGM SW Release'].strip())

            return sw_version

    # return torrent server version
    def get_tss_version(self):
        if "Torrent_Suite" not in self.version_data or not self.version_data['Torrent_Suite'].strip():
            self.logger.warning("TSS Version not in data")
            return None
        else:
            tss_version = unicode(self.version_data['Torrent_Suite'].strip())

            return tss_version

    # return start time
    def get_start_time(self):
        if "Start Time" not in self.explog_data or not self.explog_data['Start Time'].strip():
            self.logger.warning("Start Time not in explog_data")
            return None
        else:
            start_time = unicode(self.explog_data['Start Time'].strip())
            try:
                 start_time_obj = datetime.strptime(start_time, '%c')
            except ValueError:
                start_time_obj = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')

            start_time = start_time_obj

            return start_time

    # return start time
    def get_end_time(self):
        if "End Time" not in self.explog_data or not self.explog_data['End Time'].strip():
            self.logger.warning("End Time not in explog_data")
            return None
        else:
            end_time = unicode(self.explog_data['End Time'].strip())
            try:
                end_time_obj = datetime.strptime(end_time, '%c')
            except ValueError:
                end_time_obj = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

            end_time = end_time_obj

            return end_time

    # return machine serial number
    def get_sn_number(self):
        if 'Serial Number' not in self.explog_data or not self.explog_data['Serial Number'].strip():
            self.logger.warning("Serial Number not in data")
            return None
        else:
            sn_number = unicode(self.explog_data['Serial Number'].strip())

            return sn_number