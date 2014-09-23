__author__ = 'Anthony Rodriguez'

import os
import json
from decimal import Decimal

'''
    Task: parse pgm metrics found in datasets_basecaller.json
'''
class Metrics_PGM_Datasets_BaseCaller_JSON(object):

    '''
        Task: init variables, calls validate_path function
        @param    archive_path:    path to the pgm archive
        @param    logger:          system logger to log errors
        @var      data:            dictionary of datasets_basecaller.json data
    '''
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

    '''
        Task: validates existence of pgm archive path
        @param    archive_path:    path to the pgm archive
        @return   '', False:       datasets_basecaller.json
        @return   data, True:      dictionary of all data in analysis.bfmask.stats or bfmask.stats whichever if found first
    '''
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "basecaller_results", "datasets_basecaller.json")
        if not os.path.exists(path):
            self.logger.warning("datasets_basecaller.json does not exist")
            return "", False
        else:
            return self.open_basecaller_json(path), True

    '''
        Task: reads datasets_basecaller.json and converts it into a dictionary
        @param    path:    path to datasets_basecaller.json
        @return   data:    dictionary of metric data
    '''
    def open_basecaller_json(self, path):
        json_data = open(path)

        data = json.load(json_data)

        json_data.close()

        return data

    '''
        Task: check to see if given path was valid
        @return    True:    valid
        @return    False:   not valid
    '''
    def is_valid(self):
        return self.valid

    '''
        Task: returns barcode set of run
        @return    barcode_set:    barcode set of run
        @return    None:           data not found
    '''
    def get_barcode_set(self):
        if "barcode_config" not in self.data or "barcode_id" not in self.data['barcode_config'] or not self.data['barcode_config']['barcode_id'].strip():
            self.logger.warning("Barcode set information missing")
            return None
        else:
            barcode_set = unicode(self.data['barcode_config']['barcode_id'].strip())

            return barcode_set