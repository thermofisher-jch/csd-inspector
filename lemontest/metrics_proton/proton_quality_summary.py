__author__ = 'Anthony Rodriguez'

import os
from decimal import Decimal

'''
    Task: parse proton metrics found in quality.summary
'''
class Metrics_Proton_Quality_Summary(object):

    '''
        Task: init variables, calls validate_path functions for quality.summary
        @param    archive_path:    path to the proton archive
        @param    logger:          system logger to log errors
        @var      data:            dictionary of quality.summary data
    '''
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

    '''
        Task: validates existence of proton archive path
        @param    archive_path:    path to the proton archive
        @return   '', False:       quality.summary not found
        @return   data, True:      dictionary of all data in quality.summary
    '''
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "basecaller_results", "quality.summary")
        if not os.path.exists(path):
            self.logger.warning("quality.summary does not exist")
            return "", False
        else:
            return self.open_quality_summary(path), True

    '''
        Task: reads quality.summary and converts it into a dictionary
        @param    path:    path to quality.summary
        @return   data:    dictionary of metric data
    '''
    def open_quality_summary(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split(" = ", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data

    '''
        Task: check to see if given quality.summary path was valid
        @return    True:    valid
        @return    False:   not valid
    '''
    def is_valid(self):
        return self.valid

    '''
        Task: returns signal to noise ratio of run
        @return    system_snr:    signal to noise ratio of run
        @return    None:          data not found
    '''
    def get_system_snr(self):
        if "System SNR" not in self.data or not self.data['System SNR'].strip():
            self.logger.warning("System SNR not in data")
            return None
        else:
            system_snr = Decimal(self.data["System SNR"])

            return system_snr

    '''
        Task: returns number of bases at Q0
        @return    total_bases:    number of bases at Q0
        @return    None:           data not found
    '''
    def get_total_bases(self):
        if "Number of Bases at Q0" not in self.data or not self.data['Number of Bases at Q0'].strip():
            self.logger.warning("Total Bases not in data")
            return None
        else:
            total_bases = Decimal(self.data["Number of Bases at Q0"])

            return total_bases

    '''
        Task: returns number of reads at Q0
        @return    total_reads:    number of reads at Q0
        @return    None:           data not found
    '''
    def get_total_reads(self):
        if "Number of Reads at Q0" not in self.data or not self.data['Number of Reads at Q0'].strip():
            self.logger.warning("Total reads not in data")
            return None
        else:
            total_reads = Decimal(self.data["Number of Reads at Q0"])

            return total_reads

    '''
        Task: returns mean read length of run
        @return    mean_read_length:    mean read length of run
        @return    None:                data not found
    '''
    def get_mean_read_length(self):
        if "Mean Read Length at Q0" not in self.data or not self.data['Mean Read Length at Q0'].strip():
            self.logger.warning("Mean Read Length not in data")
            return None
        else:
            mean_read_length = Decimal(self.data["Mean Read Length at Q0"])

            return mean_read_length