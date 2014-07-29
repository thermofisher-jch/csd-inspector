'''
Author: Anthony Rodriguez
'''
import os
import json
from decimal import Decimal

class Metrics_Proton_BaseCaller_JSON(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path) 

    # validate archive path
    def validate_path(self, archive_path):
        path = os.path.join(archive_path, "basecaller_results", "BaseCaller.json")
        if not os.path.exists(path):
            self.logger.warning("BaseCaller.json does not exist")
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

    # return filtered polyclonal
    def get_polyclonal(self):
        if "BeadSummary" not in self.data or "lib" not in self.data["BeadSummary"] or "polyclonal" not in self.data["BeadSummary"]["lib"] or not self.data["BeadSummary"]["lib"]["polyclonal"]:
            self.logger.warning("Information missing from BaseCaller.json")
            return None
        else:
            polyclonal = Decimal(self.data["BeadSummary"]["lib"]["polyclonal"])

            return polyclonal

    # return filtered polyclonal percentage
    def get_polyclonal_pct(self, library_wells):
        if library_wells and library_wells != 0:
            if "BeadSummary" not in self.data or "lib" not in self.data["BeadSummary"] or "polyclonal" not in self.data["BeadSummary"]["lib"] or not self.data["BeadSummary"]["lib"]["polyclonal"]:
                self.logger.warning("Information missing from BaseCaller.json")
                return None
            else:
                polyclonal = Decimal(self.data["BeadSummary"]["lib"]["polyclonal"])
                polyclonal = Decimal(polyclonal / library_wells) * 100

                return polyclonal
        else:
            self.logger.warning("Library Wells missing or is 0")
            return None

    # return filtered primer dimer
    def get_primer_dimer(self):
        if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "filtered_primer_dimer" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["filtered_primer_dimer"]:
            self.logger.warning("Information missing from BaseCaller.json")
            return None
        else:
            primer_dimer = Decimal(self.data["Filtering"]["LibraryReport"]["filtered_primer_dimer"])

            return primer_dimer

    # return primer dimer percentage
    def get_primer_dimer_pct(self, library_wells):
        if library_wells and library_wells != 0:
            if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "filtered_primer_dimer" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["filtered_primer_dimer"]:
                self.logger.warning("Information missing from BaseCaller.json")
                return None
            else:
                primer_dimer = Decimal(self.data["Filtering"]["LibraryReport"]["filtered_primer_dimer"])
                primer_dimer = Decimal(primer_dimer / library_wells) * 100

                return primer_dimer
        else:
            self.logger.warning("Library Wells missing or is 0")
            return None

    # return filtered low quality
    def get_low_quality(self):
        if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "filtered_low_quality" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["filtered_low_quality"]:
            self.logger.warning("Information missing from BaseCaller.json")
            return None
        else:
            low_quality = Decimal(self.data["Filtering"]["LibraryReport"]["filtered_low_quality"])

            return low_quality

    # return low quality
    def get_low_quality_pct(self, library_wells):
        if library_wells and library_wells != 0:
            if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "filtered_low_quality" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["filtered_low_quality"]:
                self.logger.warning("Information missing from BaseCaller.json")
                return None
            else:
                low_quality = Decimal(self.data["Filtering"]["LibraryReport"]["filtered_low_quality"])
                low_quality = Decimal(low_quality / library_wells) * 100

                return low_quality
        else:
            self.logger.warning("Library Wells missing or is 0")
            return None

    # return filtered usable reads
    def get_usable_reads(self):
        if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "final_library_reads" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["final_library_reads"]:
            self.logger.warning("Information missing from BaseCaller.json")
            return None
        else:
            useable_reads = Decimal(self.data["Filtering"]["LibraryReport"]["final_library_reads"])

            return useable_reads

    # return usable reads percentage
    def get_usable_reads_pct(self, library_wells):
        if library_wells and library_wells != 0:
            if "Filtering" not in self.data or "LibraryReport" not in self.data["Filtering"] or "final_library_reads" not in self.data["Filtering"]["LibraryReport"] or not self.data["Filtering"]["LibraryReport"]["final_library_reads"]:
                self.logger.warning("Information missing from BaseCaller.json")
                return None
            else:
                library_reads = Decimal(self.data["Filtering"]["LibraryReport"]["final_library_reads"])
                useable_reads = Decimal(library_reads / library_wells) * 100

                return useable_reads
        else:
            self.logger.warning("Library Wells missing or is 0")
            return None
