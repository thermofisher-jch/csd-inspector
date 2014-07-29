'''
Author: Anthony Rodriguez
'''
import os
from decimal import Decimal

class Metrics_PGM_Explog(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

    # validate path existence
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "explog_final.txt")
        if not os.path.exists(path):
            self.logger.warning("explog_final.txt not found")
            return "", False
        else:
            return self.open_explog(path), True

    # open corresponding file
    def open_explog(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split(": ", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data

    # return True if archive path is valid, and contains explog_final.txt
    # return False otherwise
    def is_valid(self):
        return self.valid

    # return PGM Temperature as a decimal
    # or log error message and return Null value
    def get_pgm_temperature(self):
        if "PGMTemperature" not in self.data or not self.data['PGMTemperature'].strip():
            self.logger.warning("PGM Temperature not in data")
            return None
        else:
            temperature = Decimal(self.data["PGMTemperature"].strip().split(" - ")[1])

            return temperature

    # return PGM Pressure as a decimal
    # or log error message and return Null value
    def get_pgm_pressure(self):
        if "PGMPressure" not in self.data or not self.data['PGMPressure'].strip():
            self.logger.warning("PGM Pressure not in data")
            return None
        else:
            pressure = Decimal(self.data["PGMPressure"].strip().split(" - ")[1])

            return pressure

    # return Chip Temperature as a decimal
    # or log error message and return Null value
    def get_chip_temperature(self):
        if "ChipTemperature" not in self.data or not self.data['ChipTemperature'].strip():
            self.logger.warning("Chip Temperature not in data")
            return None
        else:
            temperature = Decimal(self.data["ChipTemperature"].strip().split(" - ")[1])

            return temperature

    # return Chip Noise as a decimal
    # or log error message and return Null value
    def get_chip_noise(self):
        if "Noise_90pct" not in self.data or not self.data['Noise_90pct'].strip():
            self.logger.warning("Noise_90pct not in data")
            return None
        else:
            noise = Decimal(self.data["Noise_90pct"])

            return noise

    # return gain
    def get_gain(self):
        if "Gain" not in self.data or not self.data['Gain'].strip():
            self.logger.warning("Gain not it data")
            return None
        else:
            chip_gain = Decimal(self.data["Gain"])

            return chip_gain

    # return Run Type
    def get_cycles(self):
        if "Cycles" not in self.data or not self.data['Cycles'].strip():
            self.logger.warning("Cycles not in data")
            return None
        else:
            run_type = unicode(self.data["Cycles"].strip())

            return run_type

    # return Run Type
    def get_flows(self):
        if "Flows" not in self.data or not self.data['Flows'].strip():
            self.logger.warning("Flows not in data")
            return None
        else:
            run_type = unicode(self.data["Flows"].strip())

            return run_type

    # return chip type
    def get_chip_type(self):
        if "ChipType" not in self.data or not self.data['ChipType'].strip():
            self.logger.warning("Chip Type not in data")
            return None
        else:
            chip_type = unicode(self.data["ChipType"].strip())

            return chip_type

    # return Run Type
    def get_run_type(self):
        if "RunType" not in self.data or not self.data['RunType'].strip():
            self.logger.warning("Run Type not in data")
            return None
        else:
            run_type = unicode(self.data["RunType"].strip())

            return run_type

    # return reference library
    def get_reference(self):
        if 'Library' not in self.data or not self.data['Library'].strip():
            self.logger.warning("Reference Library Info not in data")
            return None
        else:
            reference = unicode(self.data['Library'].strip())

            return reference

    # return sequencing kit information
    def get_seq_kit(self):
        if "SeqKitDesc" not in self.data or not self.data['SeqKitDesc'].strip():
            if "SeqKitPlanDesc" not in self.data or not self.data['SeqKitPlanDesc'].strip():
                self.logger.warning("Sequencing Kit information missing from explog")
                return None
            else:
                seq_kit = unicode(self.data["SeqKitPlanDesc"].strip())
                
                return seq_kit

        else:
            seq_kit = unicode(self.data["SeqKitDesc"].strip())

            return seq_kit

    # return Seq Kit Lot
    def get_seq_kit_lot(self):
        if "SeqKitLot" not in self.data or not self.data['SeqKitLot'].strip():
            self.logger.warning("Seq Kit Lot not in data")
            return None
        else:
            seq_kit_lot = unicode(self.data['SeqKitLot'].strip())

            return seq_kit_lot

    # return software Version
    def get_sw_version(self):
        if "PGM SW Release" not in self.data or not self.data['PGM SW Release'].strip():
            self.logger.warning("Software Version not in data")
            return None
        else:
            sw_version = unicode(self.data['PGM SW Release'].strip())

            return sw_version

    # return torrent server version
    def get_tss_version(self):
        version_path = os.path.join(self.archive_path, "version.txt")
        if not os.path.exists(version_path):
            self.logger.warning("version.txt missing from archive")
        else:
            line = open(version_path).readline()
            version = line.split('=')[-1].strip()
            version = unicode(version)

        if version:
            return version
        else:
            self.logger.warning("version information missing from version.txt")
            return None