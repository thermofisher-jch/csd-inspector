'''
Author: Anthony Rodriguez
File: metrics_pgm.py
Created: 9 July 2014
Last Modified: 11 July 2014
'''
import sys
import os
from decimal import Decimal

class Metrics_PGM_Explog(object):
        
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
    
    # return PGM Temperature as a decimal
    # or log error message and return Null value
    def get_pgm_temperature(self):
        if "PGMTemperature" not in self.data:
            self.logger.warning("PGM Temperature not in data")
            return None
        else:
            temperature = Decimal(self.data["PGMTemperature"].split(" - ")[1])
            
            return temperature
    
    # return PGM Pressure as a decimal
    # or log error message and return Null value
    def get_pgm_pressure(self):
        if "PGMPressure" not in self.data:
            self.logger.warning("PGM Pressure not in data")
            return None
        else:
            pressure = Decimal(self.data["PGMPressure"].split(" - ")[1])
            
            return pressure
    
    # return Chip Temperature as a decimal
    # or log error message and return Null value
    def get_chip_temperature(self):
        if "ChipTemperature" not in self.data:
            self.logger.warning("Chip Temperature not in data")
            return None
        else:
            temperature = Decimal(self.data["ChipTemperature"].split(" - ")[1])
            
            return temperature
    
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
                        seq_kit = value
                        return value
        else:
            raw_kit = unicode(self.data["SeqKitDesc"]).strip()
            
            for kit, value in self.kits.items():
                    if raw_kit == kit:
                        seq_kit = value
                        return value

    # return chip type
    def get_chip_type(self):
        if "Gain" not in self.data:
            self.logger.warning("Gain not it data")
        else:
            chip_gain = Decimal(self.data["Gain"])
            
            if chip_gain >= 0.65:
                chip_version = unicode("V2")
            else:
                chip_version = unicode("V1")

        if "ChipType" not in self.data:
            self.logger.warning("Chip Type not in data")
            return None
        else:
            chip_type = unicode(self.data["ChipType"][:3] + " " + chip_version).strip()
            
            return chip_type

    # return True if archive path is valid, and contains explog_final.txt
    # return False otherwise
    def is_valid(self):
        return self.valid
    
    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)
        self.kits = {
                "(100bp) Ion Sequencing Kit": "PGM Seq 100",
                "(200bp) Ion PGM(tm) 200 Sequencing Kit": "PGM Seq 200",
                "Ion PGM IC 200 Sequencing Kit": "PGM Seq 200 IC",
                "Ion PGM Sequencing 200 Kit v2": "PGM Seq 200 v2",
                "Ion PGM Sequencing 300 Kit": "PGM Seq 300",
                "Ion PGM Sequencing 400 Kit": "PGM Seq 400",
                "Ion PGM Hi-Q Tech Access Kit": "PGM Seq Hi-Q TA"
                }
        