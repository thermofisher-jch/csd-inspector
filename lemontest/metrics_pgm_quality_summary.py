'''
Author: Anthony Rodriguez
File: metrics_pgm.py
Created: 9 July 2014
Last Modified: 10 July 2014
'''
import sys
import os
from decimal import Decimal

class Metrics_PGM_Quality_Summary(object):
    
    # validate path existence
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "basecaller_results", "quality.summary")
        if not os.path.exists(path):
            return "quality.summary does not exist", False
        else:
            return self.open_quality_summary(path), True
    
    # open corresponding file
    def open_quality_summary(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split(" = ", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data
    
    # return system signal to noise ratio
    def get_system_snr(self):
        if "System SNR" not in self.data:
            self.logger.warning("System SNR not in data")
            return None
        else:
            system_snr = Decimal(self.data["System SNR"])
            
            return system_snr
    
    # return True if archive path is valid, and contains quality.summary
    # return False otherwise
    def is_valid(self):
        return self.valid
    
    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)