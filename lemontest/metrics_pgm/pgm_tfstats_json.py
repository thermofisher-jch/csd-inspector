__author__ = 'Anthony Rodriguez'

import os
import json
from decimal import Decimal

'''
    Task: parse pgm metrics found in TFStats.json
'''
class Metrics_PGM_TFStats_JSON(object):

    '''
        Task: init variables, calls validate_path functions for TFStats.json
        @param    archive_path:    path to the pgm archive
        @param    logger:          system logger to log errors
        @var      data:            dictionary of qTFStats.json
    '''
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

    '''
        Task: validates existence of pgm archive path
        @param    archive_path:    path to the pgm archive
        @return   '', False:       TFStats.json not found
        @return   data, True:      dictionary of all data in TFStats.json
    '''
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "basecaller_results", "TFStats.json")
        if not os.path.exists(path):
            self.logger.warning("TFStats.json does not exist")
            return "", False
        else:
            return self.open_basecaller_json(path), True

    '''
        Task: reads TFStats.json and converts it into a dictionary
        @param    path:    path to TFStats.json
        @return   data:    dictionary of metric data
    '''
    def open_basecaller_json(self, path):
        json_data = open(path)

        data = json.load(json_data)

        json_data.close()

        return data

    '''
        Task: check to see if given TFStats.json path was valid
        @return    True:    valid
        @return    False:   not valid
    '''
    def is_valid(self):
        return self.valid

    '''
        Task: returns 50Q17 test fragment data as a percentage of the total for the run
        @return    pct_50q17:    number of reads at Q0
        @return    None:         data not found || total == 0
    '''
    def get_tf_50Q17_pct(self):
        if "TF_A" not in self.data or "50Q17" not in self.data['TF_A'] or "Num" not in self.data['TF_A'] or not self.data['TF_A']['50Q17'] or not self.data['TF_A']['Num']:
            self.logger.warning("50Q17 information missing from data")
            return None
        else:
            _50q17 = Decimal(self.data['TF_A']['50Q17'])
            num = Decimal(self.data['TF_A']['Num'])

            if num != 0:
                pct_50q17 = (_50q17 / num) * 100

                return pct_50q17
            else:
                return None