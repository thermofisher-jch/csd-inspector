'''
Author: Anthony Rodriguez
'''
import os
import json
from decimal import Decimal

class Metrics_Proton_Datasets_BaseCaller_JSON(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path) 

    # validate archive path
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "basecaller_results", "datasets_basecaller.json")
        if not os.path.exists(path):
            self.logger.warning("datasets_basecaller.json does not exist")
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

    # return barcode set
    def get_barcode_set(self):
        if "barcode_config" not in self.data or "barcode_id" not in self.data['barcode_config'] or not self.data['barcode_config']['barcode_id'].strip():
            self.logger.warning("Barcode set information missing")
            return None
        else:
            barcode_set = unicode(self.data['barcode_config']['barcode_id'].strip())

            return barcode_set