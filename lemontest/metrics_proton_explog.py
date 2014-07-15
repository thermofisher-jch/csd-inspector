'''
Author: Anthony Rodriguez
File: metrics_proton_explog.py
Created: 14 July 2014
Last Modified: 14 July 2014
'''
import sys
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
            raw_data = line.split(": ", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data
    
    # return True if archive path is valid, and contains explog_final.txt
    # return False otherwise
    def is_valid(self):
        return self.valid
    
    # get chip noise info
    def proton_correlated_noise(chip_noise_info):
        info = dict(x.split(":", 1) for x in chip_noise_info.split(" "))
        return Decimal(info['Cor'])
    
    # return Chip Noise as a decimal
    # or log error message and return Null value
    def get_chip_noise(self):
        if "ChipType" not in self.data:
            self.logger.warning("Chip Type not in data")
            return None
        
        chip_type = self.data["ChipType"][:3]
        
        if chip_type != '900' and "Noise_90pct" not in self.data:
            self.logger.warning("Noise_90pct not in data")
            return None
        
        elif chip_type == '900':
            if "ChipNoiseInfo" not in self.data:
                self.logger.warning("Chip Noise Info not in data")
                return None
            else:
                try:
                    chip_noise_info = self.data.get("ChipNoiseInfo", "")
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
        if "SeqKitDesc" not in self.data:
            if "SeqKitPlanDesc" not in self.data:
                self.logger.warning("Sequencing Kit information missing from explog")
                return None
            else:
                raw_kit = unicode(self.data["SeqKitPlanDesc"]).strip()
                
                for kit, value in self.kits.items():
                    if raw_kit == kit:
                        seq_kit = unicode(value)
                        return seq_kit
        else:
            raw_kit = unicode(self.data["SeqKitDesc"]).strip()
            
            for kit, value in self.kits.items():
                if raw_kit == kit:
                    seq_kit = unicode(value)
                    return seq_kit
        
    # return PGM Pressure as a decimal
    # or log error message and return Null value
    def get_proton_pressure(self):
        if "PGMPressure" not in self.data:
            if "ProtonPressure" not in self.data:
                self.logger.warning("PGMPressure nor ProtonPressure not in data")
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
        if "pres" not in self.data:
            self.logger.warning("Target Pressure not in data")
            return None
        else:
            target_pressure = Decimal(self.data["pres"])
            
            return target_pressure
        
        