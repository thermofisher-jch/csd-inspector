'''
Author: Anthony Rodriguez
'''
import os
import re
from decimal import Decimal

class Metrics_Proton_InitLog(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data_initlog, self.valid_initlog = self.validate_path_initlog(archive_path)
        self.data_basecaller, self.valid_basecaller = self.validate_path_basecaller(archive_path)

    # validate archive path
    def validate_path_initlog(self, archive_path):
        path = os.path.join(archive_path, "InitLog.txt")
        if not os.path.exists(path):
            self.logger.warning("InitLog.txt does not exist")
            return "", False
        else:
            return self.open_initlog(path), True

    # validate archive path and existence of basecaller.log
    def validate_path_basecaller(self, archive_path):
        path = os.path.join(archive_path, "basecaller_results", "basecaller.log")
        if not os.path.exists(path):
            self.logger.warning("basecaller.log does not exist")
            return "", False
        else:
            return self.open_basecaller(path), True

    # open initlog and load convert to python dict
    def open_initlog(self, path):
        start_ph = re.compile('Initial W2 pH=\d+\.\d+')
        w1_added = re.compile('Added \d+\.\d+ mL of W1 to W2')

        data = {}

        for line in open(path):
            if start_ph.match(line):
                data["start_ph"] = start_ph.match(line).group()
            elif w1_added.match(line):
                data["added"] = w1_added.match(line).group()

        return data

    # open initlog and load convert to python dict
    def open_basecaller(self, path):
        num_barcodes = re.compile('\s+Number of barcodes\s+:\s+\d+')

        data = {}

        for line in open(path):
            if num_barcodes.match(line):
                data["num_barcodes"] = num_barcodes.match(line).group().split(":")[1].strip()

        return data

    # return True if archive path is valid_initlog, and contains initlog.txt
    # return False otherwise
    def is_initlog_valid(self):
        return self.valid_initlog

    # return True if archive path is valid_initlog, and contains initlog.txt
    # return False otherwise
    def is_basecaller_valid(self):
        return self.valid_basecaller

    # return starting ph
    def get_start_ph(self):
        if 'start_ph' not in self.data_initlog or not self.data_initlog['start_ph'].strip():
            self.logger.warning("Starting pH information missing from data_initlog")
            return None
        else:
            start_ph = Decimal(self.data_initlog['start_ph'].split("=")[1])

            return start_ph

    # return end ph
    def get_end_ph(self):
        if 'end_ph' not in self.data_initlog or not self.data_initlog['end_ph'].strip():
            self.logger.warning("Ending pH information missing from data_initlog")
            return None
        else:
            end_ph = Decimal(self.data_initlog['end_ph'].split(': ')[1])

            return end_ph

    # return w1 added
    def get_w1_added(self):
        if 'added' not in self.data_initlog or not self.data_initlog['added'].strip():
            self.logger.warning("Solution Added information missing from data_initlog")
            return None
        else:
            added = Decimal(self.data_initlog['added'].split(' ')[1])

            return added

    # return number of barcode sets
    def get_num_barcodes(self):
        if "num_barcodes" not in self.data_basecaller or not self.data_basecaller['num_barcodes'].strip():
            self.logger.warning("Number of Barcodes not in data")
            return None
        else:
            num_barcodes = Decimal(self.data_basecaller['num_barcodes'])

            return num_barcodes