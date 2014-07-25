'''
Author: Anthony Rodriguez
'''
import os
from decimal import Decimal

class Metrics_Proton_Explog(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

    # validate path existence
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "explog_final.txt")
        if not os.path.exists(path):
            return "explog_final.txt not found", False
        else:
            return self.open_explog(path), True

    # open corresponding file
    def open_explog(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split(":", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data

    # return True if archive path is valid, and contains explog_final.txt
    # return False otherwise
    def is_valid(self):
        return self.valid

    # return proton temperature
    def get_proton_temperature(self):
        if "PGMTemperature" not in self.data or not self.data['PGMTemperature'].strip():
            if "ProtonTemperature" not in self.data or not self.data['ProtonTemperature'].strip():
                self.logger.warning("Proton Temperature not in data")
                return None
            else:
                temperature = Decimal(self.data['ProtonTemperature'].strip().split(" ")[1])

                return temperature
        else:
            temperature = Decimal(self.data['PGMTemperature'].strip().split(" ")[1])

            return temperature

    # return PGM Pressure as a decimal
    # or log error message and return Null value
    def get_proton_pressure(self):
        if "PGMPressure" not in self.data or not self.data['PGMPressure'].strip():
            if "ProtonPressure" not in self.data or not self.data['ProtonPressure'].strip():
                self.logger.warning("PGMPressure nor ProtonPressure in data")
                return None
            else:
                pressure = self.data["ProtonPressure"]
                pressure = Decimal(pressure.split(" ")[1])

                return pressure
        else:
            pressure = self.data["PGMPressure"]
            pressure = Decimal(pressure.split(" ")[1])

            return pressure

    # return target pressure
    def get_target_pressure(self):
        if "pres" not in self.data or not self.data['pres'].strip():
            self.logger.warning("Target Pressure not in data")
            return None
        else:
            target_pressure = Decimal(self.data["pres"])

            return target_pressure

    # return avg chip temperature
    def get_chip_temperature(self):
        if 'ChipTemp' not in self.data or not self.data['ChipTemp'].strip():
            self.logger.warning("Chip Temp not in data")
            return None
        else:
            chip_temp = Decimal(self.data['ChipTemp'])

            return chip_temp

    # return Chip Noise as a decimal
    # or log error message and return Null value
    def get_chip_noise(self):
        if "ChipNoiseInfo" not in self.data or not self.data['ChipNoiseInfo'].strip():
                self.logger.warning("Chip Noise Info not in data")
                return None
        else:
            chip_noise_info = self.data["ChipNoiseInfo"]
            chip_noise_dict = dict(x.split(":", 1) for x in chip_noise_info.split(" "))
            if "Cor" not in chip_noise_dict or not chip_noise_dict['Cor'].strip():
                self.logger.warning("Chip Noise Correlation not in data")
                return None
            else:
                noise = Decimal(chip_noise_dict['Cor'])

                return noise

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

    # return chip type
    def get_chip_type(self):
        if "ChipMainVersion" not in self.data or not self.data['ChipMainVersion'].strip():
            if "ChipVersion" not in self.data or not self.data['ChipVersion'].strip():
                if "ChipTSVersion" not in self.data or not self.data['ChipTSVersion'].strip():
                    if "TsChipType" not in self.data or not self.data['TsChipType'].strip():
                        self.logger.warning("Chip Type not in data")
                        return None
                    else:
                        chip_type = unicode(self.data['TsChipType'].strip().split('.')[0])

                        return chip_type
                else:
                    chip_type = unicode(self.data['ChipTSVersion'].strip().split('.')[0])

                    return chip_type
            else:
                chip_type = unicode(self.data['ChipVersion'].strip().split('.')[0])

                return chip_type                
        else:
            chip_type = unicode(self.data['ChipMainVersion'].strip().split('.')[0])

            return chip_type

    # return chip gain
    def get_gain(self):
        if "ChipGain" not in self.data or not self.data['ChipGain'].strip():
            self.logger.warning("Chip Gain not in data")
            return None
        else:
            gain = Decimal(self.data['ChipGain'])

            return gain

    # return software version
    def get_sw_version(self):
        if "Proton Release" not in self.data or not self.data['Proton Release'].strip():
            self.logger.warning("Proton SW version not in data")
            return None
        else:
            sw_version = unicode(self.data['Proton Release'].strip())
            return sw_version


# return Seq Kit Lot
    def get_seq_kit_lot(self):
        if "SeqKitLot" not in self.data or not self.data['SeqKitLot'].strip():
            self.logger.warning("Seq Kit Lot not in data")
            return None
        else:
            seq_kit_lot = unicode(self.data['SeqKitLot'].strip())

            return seq_kit_lot

    # return Run Type
    def get_run_type(self):
        if "RunType" not in self.data or not self.data['RunType'].strip():
            self.logger.warning("Run Type not in data")
            return None
        else:
            run_type = unicode(self.data["RunType"].strip())

            return run_type

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

    # return tss version
    def get_tss_version(self):
        version_path = os.path.join(self.archive_path, "version.txt")
        if not os.path.exists(version_path):
            self.logger.warning("version.txt missing from archive")
            return None
        else:
            line = open(version_path).readline()
            version = line.split('=')[-1].strip()
            version = unicode(version)

        if version:
            return version
        else:
            self.logger.warning("version information missing from version.txt")
            return None