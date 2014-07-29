'''
Author: Anthony Rodriguez
'''
import os
from decimal import Decimal

class Metrics_Proton_Bfmask_Stats(object):

    # initialize
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.data, self.valid = self.validate_path(archive_path)

    # validate path existence
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

    # open corresponding file
    def open_bfmask_stats(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split(" = ", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data

    # return True if archive path is valid, and contains analysis.bfmask.stats or bfmask.stats
    # return False otherwise
    def is_valid(self):
        return self.valid

    # return ISP loading percentage
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

    # return ISP Wells
    def get_isp_wells(self):
        if "Bead Wells" not in self.data or not self.data["Bead Wells"].strip():
            self.logger.warning("IPS Wells not in data")
            return None
        else:
            isp_wells = Decimal(self.data["Bead Wells"])
            
            return isp_wells

    # return Live Wells
    def get_live_wells(self):
        if "Live Beads" not in self.data or not self.data['Live Beads'].strip():
            self.logger.warning("Live wells not in data")
            return None
        else:
            live_wells = Decimal(self.data['Live Beads'])

            return live_wells

    # return Library Wells
    def get_library_wells(self):
        if "Library Beads" not in self.data or not self.data['Library Beads'].strip():
            self.logger.warning('Library Beads not in data')
            return None
        else:
            library_wells = Decimal(self.data['Library Beads'])

            return library_wells

    # return Test Fragment Beads
    def get_test_fragment(self):
        if "Test Fragment Beads" not in self.data or not self.data['Test Fragment Beads'].strip():
            self.logger.warning("Test Fragment Beads not in data")
            return None
        else:
            test_fragment = Decimal(self.data["Test Fragment Beads"])

            return test_fragment