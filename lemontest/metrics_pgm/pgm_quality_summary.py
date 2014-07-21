'''
Author: Anthony Rodriguez
'''
import os
from decimal import Decimal

class Metrics_PGM_Quality_Summary(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

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

    # return True if archive path is valid, and contains quality.summary
    # return False otherwise
    def is_valid(self):
        return self.valid

    # return system signal to noise ratio
    def get_system_snr(self):
        if "System SNR" not in self.data or not self.data['System SNR'].strip():
            self.logger.warning("System SNR not in data")
            return None
        else:
            system_snr = Decimal(self.data["System SNR"])
            
            return system_snr

    # return Total Bases
    def get_total_bases(self):
        if "Number of Bases at Q0" not in self.data or not self.data['Number of Bases at Q0'].strip():
            self.logger.warning("Total Bases not in data")
            return None
        else:
            total_bases = Decimal(self.data["Number of Bases at Q0"])
            
            return total_bases

    # return Total Reads
    def get_total_reads(self):
        if "Number of Reads at Q0" not in self.data or not self.data['Number of Reads at Q0'].strip():
            self.logger.warning("Total reads not in data")
            return None
        else:
            total_reads = Decimal(self.data["Number of Reads at Q0"])
            
            return total_reads

    # return Mean Read Length
    def get_mean_read_length(self):
        if "Mean Read Length at Q0" not in self.data or not self.data['Mean Read Length at Q0'].strip():
            self.logger.warning("Mean Read Length not in data")
            return None
        else:
            mean_read_length = Decimal(self.data["Mean Read Length at Q0"])
            
            return mean_read_length