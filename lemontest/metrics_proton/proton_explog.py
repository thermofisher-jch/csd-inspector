'''
Author: Anthony Rodriguez
'''
import os
from decimal import Decimal
from datetime import datetime

class Metrics_Proton_Explog(object):

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
            raw_data = line.split(":", 1)
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

    # return proton temperature
    def get_proton_temperature(self):
        if "PGMTemperature" not in self.explog_data or not self.explog_data['PGMTemperature'].strip():
            if "ProtonTemperature" not in self.explog_data or not self.explog_data['ProtonTemperature'].strip():
                self.logger.warning("Proton Temperature not in explog_data")
                return None
            else:
                temperature = Decimal(self.explog_data['ProtonTemperature'].strip().split(" ")[1])

                return temperature
        else:
            temperature = Decimal(self.explog_data['PGMTemperature'].strip().split(" ")[1])

            return temperature

    # return PGM Pressure as a decimal
    # or log error message and return Null value
    def get_proton_pressure(self):
        if "PGMPressure" not in self.explog_data or not self.explog_data['PGMPressure'].strip():
            if "ProtonPressure" not in self.explog_data or not self.explog_data['ProtonPressure'].strip():
                self.logger.warning("PGMPressure nor ProtonPressure in explog_data")
                return None
            else:
                pressure = self.explog_data["ProtonPressure"]
                pressure = Decimal(pressure.split(" ")[1])

                return pressure
        else:
            pressure = self.explog_data["PGMPressure"]
            pressure = Decimal(pressure.split(" ")[1])

            return pressure

    # return target pressure
    def get_target_pressure(self):
        if "pres" not in self.explog_data or not self.explog_data['pres'].strip():
            self.logger.warning("Target Pressure not in explog_data")
            return None
        else:
            target_pressure = Decimal(self.explog_data["pres"])

            return target_pressure

    # return avg chip temperature
    def get_chip_temperature(self):
        if 'ChipTemp' not in self.explog_data or not self.explog_data['ChipTemp'].strip():
            self.logger.warning("Chip Temp not in explog_data")
            return None
        else:
            chip_temp = Decimal(self.explog_data['ChipTemp'])

            return chip_temp

    # return Chip Noise as a decimal
    # or log error message and return Null value
    def get_chip_noise(self):
        if "ChipNoiseInfo" not in self.explog_data or not self.explog_data['ChipNoiseInfo'].strip():
                self.logger.warning("Chip Noise Info not in explog_data")
                return None
        else:
            chip_noise_info = self.explog_data["ChipNoiseInfo"]
            chip_noise_dict = dict(x.split(":", 1) for x in chip_noise_info.split(" "))
            if "Cor" not in chip_noise_dict or not chip_noise_dict['Cor'].strip():
                self.logger.warning("Chip Noise Correlation not in explog_data")
                return None
            else:
                noise = Decimal(chip_noise_dict['Cor'])

                return noise

    # return chip gain
    def get_gain(self):
        if "ChipGain" not in self.explog_data or not self.explog_data['ChipGain'].strip():
            self.logger.warning("Chip Gain not in explog_data")
            return None
        else:
            gain = Decimal(self.explog_data['ChipGain'])

            return gain

    # return Run Type
    def get_flows(self):
        if "Flows" not in self.explog_data or not self.explog_data['Flows'].strip():
            self.logger.warning("Flows not in explog_data")
            return None
        else:
            run_type = unicode(self.explog_data["Flows"].strip())

            return run_type

    # return Run Type
    def get_cycles(self):
        if "Cycles" not in self.explog_data or not self.explog_data['Cycles'].strip():
            self.logger.warning("Cycles not in explog_data")
            return None
        else:
            run_type = unicode(self.explog_data["Cycles"].strip())

            return run_type

    # return chip type
    def get_chip_type(self):
        if "ChipMainVersion" not in self.explog_data or not self.explog_data['ChipMainVersion'].strip():
            if "ChipVersion" not in self.explog_data or not self.explog_data['ChipVersion'].strip():
                if "ChipTSVersion" not in self.explog_data or not self.explog_data['ChipTSVersion'].strip():
                    if "TsChipType" not in self.explog_data or not self.explog_data['TsChipType'].strip():
                        self.logger.warning("Chip Type not in explog_data")
                        return None
                    else:
                        chip_type = unicode(self.explog_data['TsChipType'].strip().split('.')[0])

                        return chip_type
                else:
                    chip_type = unicode(self.explog_data['ChipTSVersion'].strip().split('.')[0])

                    return chip_type
            else:
                chip_type = unicode(self.explog_data['ChipVersion'].strip().split('.')[0])

                return chip_type
        else:
            chip_type = unicode(self.explog_data['ChipMainVersion'].strip().split('.')[0])

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

    # return software version
    def get_sw_version(self):
        if "Proton Release" not in self.explog_data or not self.explog_data['Proton Release'].strip():
            self.logger.warning("Proton SW version not in explog_data")
            return None
        else:
            sw_version = unicode(self.explog_data['Proton Release'].strip())

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
            start_time_obj = datetime.strptime(start_time, '%m/%d/%Y %H:%M:%S')
            start_time = start_time_obj

            return start_time

    # return start time
    def get_end_time(self):
        if "End Time" not in self.explog_data or not self.explog_data['End Time'].strip():
            self.logger.warning("End Time not in explog_data")
            return None
        else:
            end_time = unicode(self.explog_data['End Time'].strip())
            end_time_obj = datetime.strptime(end_time, '%m/%d/%Y %H:%M:%S')
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

    # return barcode id
    def get_barcode_set(self):
        if "barcodeId" not in self.explog_data or not self.explog_data['barcodeId'].strip():
            self.logger.warning('barcodeId not in explog_data')
            return None
        else:
            barcode_set = unicode(self.explog_data['barcodeId'].strip())

            return barcode_set