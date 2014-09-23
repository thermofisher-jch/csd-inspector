__author__ = 'Anthony Rodriguez'

import os
from decimal import Decimal

'''
    Task: parse proton metrics found in analysis.bfmask.stats or bfmask.stats if former was not found
'''
class Metrics_Proton_Bfmask_Stats(object):

    '''
        Task: init variables, calls validate_path function
        @param    archive_path:    path to the proton archive
        @param    logger:          system logger to log errors
        @var      data:            dictionary of analysis.bfmask.stats or bfmask.stats data
    '''
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

    '''
        Task: validates existence of proton archive path
        @param    archive_path:    path to the proton archive
        @return   '', False:       analysis.bfmask.stats and bfmask.stats do not exist
        @return   data, True:      dictionary of all data in analysis.bfmask.stats or bfmask.stats whichever if found first
    '''
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "sigproc_results", "analysis.bfmask.stats")
        if not os.path.exists(path):
            path = os.path.join(archive_path, "sigproc_results", "bfmask.stats")
            if not os.path.exists(path):
                self.logger.warning("analysis.bfmask.stats and bfmask.stats both missing")
                return "", False
            else:
                return self.open_bfmask_stats(path), True
        else:
            return self.open_bfmask_stats(path), True

    '''
        Task: reads analysis.bfmask.stats or bfmask.stats and converts it into a dictionary
        @param    path:    path to analysis.bfmask.stats or bfmask.stats
        @return   data:    dictionary of metric data
    '''
    def open_bfmask_stats(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split(" = ", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data

    '''
        Task: check to see if given path was valid
        @return    True:    valid
        @return    False:   not valid
    '''
    def is_valid(self):
        return self.valid

    '''
        Task: returns isp loading percentage of run
        @return    isp_loading:    isp loading percentage of run
        @return    None:           data not found || excluded wells >= total wells
    '''
    def get_isp_loading(self):
        if "Bead Wells" not in self.data or "Total Wells" not in self.data or "Excluded Wells" not in self.data or not self.data["Bead Wells"].strip() or not self.data["Total Wells"].strip() or not self.data["Excluded Wells"].strip():
            self.logger.warning("One or more needed fields is missing")
            return None
        else:
            bead_wells = Decimal(self.data["Bead Wells"])
            total_wells = Decimal(self.data["Total Wells"])
            excluded_wells = Decimal(self.data["Excluded Wells"])

            if (total_wells - excluded_wells) <= 0:
                self.logger.warning("All wells excluded")
                return None
            else:
                isp_loading = (bead_wells / (total_wells - excluded_wells)) * 100

            return isp_loading

    '''
        Task: returns total wells with isp in run
        @return    isp_wells:    total wells with isp in run
        @return    None:         data not found
    '''
    def get_isp_wells(self):
        if "Bead Wells" not in self.data or not self.data["Bead Wells"].strip():
            self.logger.warning("IPS Wells not in data")
            return None
        else:
            isp_wells = Decimal(self.data["Bead Wells"])

            return isp_wells

    '''
        Task: returns total live wells in run
        @return    live_wells:    total live wells in run
        @return    None:          data not found
    '''
    def get_live_wells(self):
        if "Live Beads" not in self.data or not self.data['Live Beads'].strip():
            self.logger.warning("Live wells not in data")
            return None
        else:
            live_wells = Decimal(self.data['Live Beads'])

            return live_wells

    '''
        Task: returns total library wells in run
        @return    library_wells:    total library wells in run
        @return    None:             data not found
    '''
    def get_library_wells(self):
        if "Library Beads" not in self.data or not self.data['Library Beads'].strip():
            self.logger.warning('Library Beads not in data')
            return None
        else:
            library_wells = Decimal(self.data['Library Beads'])

            return library_wells

    '''
        Task: returns test fragment of run
        @return    test_fragment:    test fragment of run
        @return    None:             data not found
    '''
    def get_test_fragment(self):
        if "Test Fragment Beads" not in self.data or not self.data['Test Fragment Beads'].strip():
            self.logger.warning("Test Fragment Beads not in data")
            return None
        else:
            test_fragment = Decimal(self.data["Test Fragment Beads"])

            return test_fragment