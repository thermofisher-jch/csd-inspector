'''
Author: Anthony Rodriguez
'''
import os
import json
from decimal import Decimal

class Metrics_Proton_TFStats_JSON(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

    # validate archive path
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "basecaller_results", "TFStats.json")
        if not os.path.exists(path):
            self.logger.warning("TFStats.json does not exist")
            return "", False
        else:
            return self.open_basecaller_json(path), True

    # open BaseCaller.json and load convert to python dict
    def open_basecaller_json(self, path):
        json_data = open(path)

        data = json.load(json_data)

        json_data.close()

        return data

    # return True if archive path is valid, and contains BaseCaller.json
    # return False otherwise
    def is_valid(self):
        return self.valid

    # return percent 50Q17
    def get_tf_50Q17_pct(self):
        if "TF_C" not in self.data or "50Q17" not in self.data['TF_C'] or "Num" not in self.data['TF_C'] or not self.data['TF_C']['50Q17'] or not self.data['TF_C']['Num']:
            self.logger.warning("50Q17 information missing from data")
            return None
        else:
            _50q17 = Decimal(self.data['TF_C']['50Q17'])
            num = Decimal(self.data['TF_C']['Num'])

            if num != 0:
                pct_50q17 = (_50q17 / num) * 100

                return pct_50q17
            else:
                return None