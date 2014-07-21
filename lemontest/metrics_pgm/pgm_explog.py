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
            return "explog_final.txt not found", False
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

    # get chip noise info
    def proton_correlated_noise(chip_noise_info):
        info = dict(x.split(":", 1) for x in chip_noise_info.split(" "))
        return Decimal(info['Cor'])

    # return Chip Noise as a decimal
    # or log error message and return Null value
    def get_chip_noise(self):
        if "ChipType" not in self.data or not self.data['ChipType'].strip():
            self.logger.warning("Chip Type not in data")
            return None

        chip_type = self.data["ChipType"].strip()[:3]

        if chip_type != '900' and ("Noise_90pct" not in self.data or not self.data['Noise_90pct'].strip()):
            self.logger.warning("Noise_90pct not in data")
            return None

        elif chip_type == '900':
            if "ChipNoiseInfo" not in self.data or not self.data['ChipNoiseInfo'].strip():
                self.logger.warning("Chip Noise Info not in data")
                return None
            else:
                try:
                    chip_noise_info = self.data.get("ChipNoiseInfo", u'')
                    noise = self.proton_correlated_noise(chip_noise_info)
                except (ValueError, KeyError) as err:
                    self.logger.warning("Correlated Chip Noise Info not in data")
                    return None

            return noise
        else:
            noise = Decimal(self.data["Noise_90pct"])

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
        if "ChipType" not in self.data or not self.data['ChipType'].strip():
            self.logger.warning("Chip Type not in data")
            return None
        else:
            chip_type = unicode(self.data["ChipType"].strip()[:3])

            return chip_type

    # return gain
    def get_gain(self):
        if "Gain" not in self.data or not self.data['Gain'].strip():
            self.logger.warning("Gain not it data")
            return None
        else:
            chip_gain = Decimal(self.data["Gain"])

            return chip_gain

    # return TSS Version
    def get_tss_version(self):
        if "PGM SW Release" not in self.data or not self.data['PGM SW Release'].strip():
            self.logger.warning("TSS Version not in data")
            return None
        else:
            tss_version = unicode(self.data['PGM SW Release'].strip())

            return tss_version

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