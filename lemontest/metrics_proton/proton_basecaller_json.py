__author__ = 'Anthony Rodriguez'

import os
import json
from decimal import Decimal

'''
    Task: parse proton metrics found in BaseCaller.json
'''
class Metrics_Proton_BaseCaller_JSON(object):

    '''
        Task: init variables, calls validate_path function
        @param    archive_path:    path to the proton archive
        @param    logger:          system logger to log errors
        @var      data:            dictionary of BaseCaller.json data
    '''
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

    '''
        Task: validates existence of proton archive path
        @param    archive_path:    path to the proton archive
        @return   '', False:       BaseCaller.json does not exist
        @return   data, True:      dictionary of all data in BaseCaller.json
    '''
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "basecaller_results", "BaseCaller.json")
        if not os.path.exists(path):
            self.logger.warning("BaseCaller.json does not exist")
            return '', False
        else:
            return self.open_basecaller_json(path), True

    '''
        Task: reads BaseCaller.json and converts it into a dictionary
        @param    path:    path to BaseCaller.json
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
        Task: returns total filtered polyclonal of run
        @return    polyclonal:    total filtered polyclonal of run
        @return    None:          data not found
    '''
    def get_polyclonal(self):
        if "BeadSummary" not in self.data or "lib" not in self.data["BeadSummary"] or "polyclonal" not in self.data["BeadSummary"]["lib"] or not self.data["BeadSummary"]["lib"]["polyclonal"]:
            self.logger.warning("Polyclonal Information missing from BaseCaller.json")
            return None
        else:
            polyclonal = Decimal(self.data["BeadSummary"]["lib"]["polyclonal"])

            return polyclonal

    '''
        Task: returns polyclonal percentage of run
        @param     library_wells:        total library wells for the run to calculate percentage
        @return    polyclonal_pct:       filtered polyclonal percentage of run
        @return    None:                 data not found || library_wells == 0 || library_wells not set
    '''
    def get_polyclonal_pct(self, library_wells):
        if library_wells and library_wells != 0:
            if "BeadSummary" not in self.data or "lib" not in self.data["BeadSummary"] or "polyclonal" not in self.data["BeadSummary"]["lib"] or not self.data["BeadSummary"]["lib"]["polyclonal"]:
                self.logger.warning("Polyclonal Information missing from BaseCaller.json")
                return None
            else:
                polyclonal = Decimal(self.data["BeadSummary"]["lib"]["polyclonal"])
                polyclonal_pct = Decimal(polyclonal / library_wells) * 100

                return polyclonal_pct
        else:
            self.logger.warning("Library Wells missing or is 0")
            return None

    '''
        Task: returns total primer dimer of run
        @return    primer_dimer:    total primer_dimer of run
        @return    None:            data not found
    '''
    def get_primer_dimer(self):
        if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "filtered_primer_dimer" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["filtered_primer_dimer"]:
            self.logger.warning("Primer Dimer Information missing from BaseCaller.json")
            return None
        else:
            primer_dimer = Decimal(self.data["Filtering"]["LibraryReport"]["filtered_primer_dimer"])

            return primer_dimer

    '''
        Task: returns primer dimer percentage of run
        @param     library_wells:        total library wells for the run to calculate percentage
        @return    primer_dimer_pct:     primer_dimer percentage of run
        @return    None:                 data not found || library_wells == 0 || library_wells not set
    '''
    def get_primer_dimer_pct(self, library_wells):
        if library_wells and library_wells != 0:
            if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "filtered_primer_dimer" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["filtered_primer_dimer"]:
                self.logger.warning("Primer Dimer Information missing from BaseCaller.json")
                return None
            else:
                primer_dimer = Decimal(self.data["Filtering"]["LibraryReport"]["filtered_primer_dimer"])
                primer_dimer_pct = Decimal(primer_dimer / library_wells) * 100

                return primer_dimer_pct
        else:
            self.logger.warning("Library Wells missing or is 0")
            return None

    '''
        Task: returns filtered low quality of run
        @return    low_quality:    filtered low quality of run
        @return    None:           data not found
    '''
    def get_low_quality(self):
        if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "filtered_low_quality" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["filtered_low_quality"]:
            self.logger.warning("Low Quality Information missing from BaseCaller.json")
            return None
        else:
            low_quality = Decimal(self.data["Filtering"]["LibraryReport"]["filtered_low_quality"])

            return low_quality

    '''
        Task: returns filtered low quality percentage of run
        @param     library_wells:      total library wells for the run to calculate percentage
        @return    low_quality_pct:    filtered low quality percentage of run
        @return    None:                 data not found || library_wells == 0 || library_wells not set
    '''
    def get_low_quality_pct(self, library_wells):
        if library_wells and library_wells != 0:
            if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "filtered_low_quality" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["filtered_low_quality"]:
                self.logger.warning("Low Quality Information missing from BaseCaller.json")
                return None
            else:
                low_quality = Decimal(self.data["Filtering"]["LibraryReport"]["filtered_low_quality"])
                low_quality_pct = Decimal(low_quality / library_wells) * 100

                return low_quality_pct
        else:
            self.logger.warning("Library Wells missing or is 0")
            return None

    '''
        Task: returns total usable reads of run
        @return    useable_reads:    total usable reads of run
        @return    None:             data not found
    '''
    def get_usable_reads(self):
        if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "final_library_reads" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["final_library_reads"]:
            self.logger.warning("Usable Reads Information missing from BaseCaller.json")
            return None
        else:
            useable_reads = Decimal(self.data["Filtering"]["LibraryReport"]["final_library_reads"])

            return useable_reads

    '''
        Task: returns filtered low quality percentage of run
        @param     library_wells:        total library wells for the run to calculate percentage
        @return    useable_reads_pct:    usable reads percentage of run
        @return    None:                 data not found || library_wells == 0 || library_wells not set
    '''
    def get_usable_reads_pct(self, library_wells):
        if library_wells and library_wells != 0:
            if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "final_library_reads" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["final_library_reads"]:
                self.logger.warning("Usable Reads Information missing from BaseCaller.json")
                return None
            else:
                library_reads = Decimal(self.data["Filtering"]["LibraryReport"]["final_library_reads"])
                useable_reads_pct = Decimal(library_reads / library_wells) * 100

                return useable_reads_pct
        else:
            self.logger.warning("Library Wells missing or is 0")
            return None
