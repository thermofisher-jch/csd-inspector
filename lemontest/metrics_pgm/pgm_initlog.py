'''
Author: Anthony Rodriguez
'''
import os
import re
from decimal import Decimal

class Metrics_PGM_InitLog(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path) 

    # validate archive path
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "InitLog.txt")
        if not os.path.exists(path):
            return "InitLog.txt does not exist", False
        else:
            return self.open_basecaller_json(path), True

    # open BaseCaller.json and load convert to python dict
    def open_basecaller_json(self, path):
        start_ph = re.compile('1\) W2 pH=\d+\.\d+')
        w1_added = re.compile('Added \d+\.\d+ mL of W1 to W2')
        end_ph = re.compile('RawTraces W2: \d+\.\d+')

        data = {}

        for line in open(path):
            if start_ph.match(line):
                data["start_ph"] = start_ph.match(line).group()
            elif w1_added.match(line):
                data["added"] = w1_added.match(line).group()
            elif end_ph.match(line):
                data["end_ph"] = end_ph.match(line).group()

        return data

    # return True if archive path is valid, and contains BaseCaller.json
    # return False otherwise
    def is_valid(self):
        return self.valid

    # return starting ph
    def get_start_ph(self):
        start_ph = Decimal(self.data['start_ph'].split("=")[1])

        return start_ph

    # return end ph
    def get_end_ph(self):
        end_ph = Decimal(self.data['end_ph'].split(': ')[1])

        return end_ph

    # return w1 added
    def get_w1_added(self):
        added = Decimal(self.data['added'].split(' ')[1])

        return added