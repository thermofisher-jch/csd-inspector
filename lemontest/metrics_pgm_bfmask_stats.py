'''
Author: Anthony Rodriguez
File: metrics_pgm.py
Created: 9 July 2014
Last Modified: 11 July 2014
'''
import sys
import os
from decimal import Decimal

class Metrics_PGM_Bfmask_Stats(object):
    
    # validate path existence
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "sigproc_results", "analysis.bfmask.stats")
        if not os.path.exists(path):
            path = os.path.join(archive_path, "sigproc_results", "bfmask.stats")
            if not os.path.exists(path):
                return "analysis.bfmask.stats and bfmask.stats both missing", False
            else:
                return self.open_bfmask_stats(path), True
        else:
            return self.open_bfmask_stats(path), True
    
    # open corresponding file
    def open_bfmask_stats(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split(" = ", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data
    
    # return ISP loading percentage
    def get_isp_loading(self):
        if "Bead Wells" not in self.data or "Total Wells" not in self.data or "Excluded Wells" not in self.data:
            self.logger.warning("One or more needed fields is missing")
            return None
        else:
            bead_wells = Decimal(self.data["Bead Wells"])
            total_wells = Decimal(self.data["Total Wells"])
            excluded_wells = Decimal(self.data["Excluded Wells"])
            
            isp_loading = (bead_wells / (total_wells - excluded_wells)) * 100
            
            return isp_loading
    
    # return True if archive path is valid, and contains quality.summary
    # return False otherwise
    def is_valid(self):
        return self.valid
    
    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)
