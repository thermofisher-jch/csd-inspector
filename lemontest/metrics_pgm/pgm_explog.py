__author__ = 'Anthony Rodriguez'

import os
from decimal import Decimal
from datetime import datetime
from __builtin__ import ValueError

'''
    Task: parse pgm metrics found in explog_final.txt and version.txt
'''
class Metrics_PGM_Explog(object):

    '''
        Task: init variables, calls validate_path functions for explog_final.txt and version.txt
        @param    archive_path:    path to the pgm archive
        @param    logger:          system logger to log errors
        @var      explog_data:     dictionary of explog_final.txt data
        @var      version_data:    dictionary of version.txt data
    '''
    def __init__(self, archive_path, logger):
        self.archive_path = archive_path
        self.logger = logger
        self.explog_data, self.explog_valid = self.validate_explog_path(archive_path)
        self.version_data, self.version_valid = self.validate_version_path(archive_path)

    '''
        Task: validates existence of pgm archive path
        @param    archive_path:    path to the pgm archive
        @return   '', False:       explog_final.txt not found
        @return   data, True:      dictionary of all data in explog_final.txt
    '''
    def validate_explog_path(self, archive_path):
        path = os.path.join(archive_path, "explog_final.txt")
        if not os.path.exists(path):
            self.logger.warning("explog_final.txt not found")
            return "", False
        else:
            return self.open_explog(path), True

    '''
        Task: validates existence of pgm archive path
        @param    archive_path:    path to the pgm archive
        @return   '', False:       version.txt not found
        @return   data, True:      dictionary of all data in version.txt
    '''
    def validate_version_path(self, archive_path):
        path = os.path.join(self.archive_path, "version.txt")
        if not os.path.exists(path):
            self.logger.warning("version.txt missing from archive")
            return "", False
        else:
            return self.open_version(path), True

    '''
        Task: reads explog_final.txt and converts it into a dictionary
        @param    path:    path to explog_final.txt
        @return   data:    dictionary of metric data
    '''
    def open_explog(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split(": ", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data

    '''
        Task: reads version.txt and converts it into a dictionary
        @param    path:    path to version.txt
        @return   data:    dictionary of metric data
    '''
    def open_version(self, path):
        data = {}
        for line in open(path):
            raw_data = line.split("=", 1)
            if len(raw_data) == 2:
                key, value = raw_data
                data[key.strip()] = value.strip()
        return data

    '''
        Task: check to see if given explog_final.txt path was valid
        @return    True:    valid
        @return    False:   not valid
    '''
    def is_explog_valid(self):
        return self.explog_valid

    '''
        Task: check to see if given version.txt path was valid
        @return    True:    valid
        @return    False:   not valid
    '''
    def is_version_valid(self):
        return self.version_valid

    '''
        Task: returns pgm temperature of run
        @return    temperature:    pgm temperature of run
        @return    None:           data not found
    '''
    def get_pgm_temperature(self):
        if "PGMTemperature" not in self.explog_data or not self.explog_data['PGMTemperature'].strip():
            self.logger.warning("PGM Temperature not in explog_data")
            return None
        else:
            temperature = Decimal(self.explog_data["PGMTemperature"].strip().split(" - ")[1])

            return temperature

    '''
        Task: returns pgm pressure of run
        @return    pressure:    pgm pressure of run
        @return    None:        data not found
    '''
    def get_pgm_pressure(self):
        if "PGMPressure" not in self.explog_data or not self.explog_data['PGMPressure'].strip():
            self.logger.warning("PGM Pressure not in explog_data")
            return None
        else:
            pressure = Decimal(self.explog_data["PGMPressure"].strip().split(" - ")[1])

            return pressure

    '''
        Task: returns chip temperature of run
        @return    temperature:    chip temperature of run
        @return    None:           data not found
    '''
    def get_chip_temperature(self):
        if "ChipTemperature" not in self.explog_data or not self.explog_data['ChipTemperature'].strip():
            self.logger.warning("Chip Temperature not in explog_data")
            return None
        else:
            temperature = Decimal(self.explog_data["ChipTemperature"].strip().split(" - ")[1])

            return temperature

    '''
        Task: returns chip noise info of run
        @return    noise:    chip noise info of run
        @return    None:     data not found
    '''
    def get_chip_noise(self):
        if "Noise_90pct" not in self.explog_data or not self.explog_data['Noise_90pct'].strip():
            self.logger.warning("Noise_90pct not in explog_data")
            return None
        else:
            noise = Decimal(self.explog_data["Noise_90pct"])

            return noise

    '''
        Task: returns chip gain info of run
        @return    chip_gain:    chip gain info of run
        @return    None:         data not found
    '''
    def get_gain(self):
        if "Gain" not in self.explog_data or not self.explog_data['Gain'].strip():
            self.logger.warning("Gain not it explog_data")
            return None
        else:
            chip_gain = Decimal(self.explog_data["Gain"])

            return chip_gain

    '''
        Task: returns cycles of run
        @return    cycles:    cycles of run
        @return    None:      data not found
    '''
    def get_cycles(self):
        if "Cycles" not in self.explog_data or not self.explog_data['Cycles'].strip():
            self.logger.warning("Cycles not in explog_data")
            return None
        else:
            cycles = unicode(self.explog_data["Cycles"].strip())

            return cycles

    '''
        Task: returns flows of run
        @return    flows:    flows of run
        @return    None:     data not found
    '''
    def get_flows(self):
        if "Flows" not in self.explog_data or not self.explog_data['Flows'].strip():
            self.logger.warning("Flows not in explog_data")
            return None
        else:
            flows = unicode(self.explog_data["Flows"].strip())

            return flows

    '''
        Task: returns chip type used in run
        @return    chip_type:    chip type used in run
        @return    None:         data not found
    '''
    def get_chip_type(self):
        if "ChipType" not in self.explog_data or not self.explog_data['ChipType'].strip():
            self.logger.warning("Chip Type not in explog_data")
            return None
        else:
            chip_type = unicode(self.explog_data["ChipType"].strip())
            if chip_type.startswith('"') and chip_type.endswith('"'):
                chip_type = chip_type[1:-1]

            return chip_type

    '''
        Task: returns run type of run
        @return    run_type:    run type if run
        @return    None:        data not found
    '''
    def get_run_type(self):
        if "RunType" not in self.explog_data or not self.explog_data['RunType'].strip():
            self.logger.warning("Run Type not in explog_data")
            return None
        else:
            run_type = unicode(self.explog_data["RunType"].strip())

            return run_type

    '''
        Task: returns reference library used in run
        @return    reference:    reference library used in run
        @return    None:         data not found || 'none' was entered
    '''
    def get_reference(self):
        if 'Library' not in self.explog_data or not self.explog_data['Library'].strip():
            self.logger.warning("Reference Library Info not in explog_data")
            return None
        else:
            reference = unicode(self.explog_data['Library'].strip())
            if reference == 'none':
                return None

            return reference

    '''
        Task: returns sequencing kit type used in run
        @return    seq_kit:    sequencing kit type used in run
        @return    None:       data not found
    '''
    def get_seq_kit(self):
        if "SeqKitDesc" not in self.explog_data or not self.explog_data['SeqKitDesc'].strip():
            if "SeqKitPlanDesc" not in self.explog_data or not self.explog_data['SeqKitPlanDesc'].strip():
                self.logger.warning("Sequencing Kit information missing from explog")
                return None
            else:
                seq_kit = unicode(self.explog_data["SeqKitPlanDesc"].strip())

                return seq_kit

        else:
            seq_kit = unicode(self.explog_data["SeqKitDesc"].strip())

            return seq_kit

    '''
        Task: returns sequencing kit lot used in run
        @return    seq_kit_lot:    sequencing kit lot used in run
        @return    None:           data not found
    '''
    def get_seq_kit_lot(self):
        if "SeqKitLot" not in self.explog_data or not self.explog_data['SeqKitLot'].strip():
            self.logger.warning("Seq Kit Lot not in explog_data")
            return None
        else:
            seq_kit_lot = unicode(self.explog_data['SeqKitLot'].strip())

            return seq_kit_lot

    '''
        Task: returns machine hardware version
        @return    pgm_hw:    machine hardware version
        @return    None:      data not found
    '''
    def get_hw_version(self):
        if "PGM HW" not in self.explog_data or not self.explog_data['PGM HW'].strip():
            self.logger.warning("PGM HW not in explog_data")
            return None
        else:
            pgm_hw = unicode(self.explog_data['PGM HW'].strip())

            return pgm_hw

    '''
        Task: returns machine software version
        @return    sw_version:    machine software version
        @return    None:          data not found
    '''
    def get_sw_version(self):
        if "PGM SW Release" not in self.explog_data or not self.explog_data['PGM SW Release'].strip():
            self.logger.warning("Software Version not in explog_data")
            return None
        else:
            sw_version = unicode(self.explog_data['PGM SW Release'].strip())

            return sw_version

    '''
        Task: returns server torrent suite version
        @return    tss_version:    server torrent suite version
        @return    None:           data not found
    '''
    def get_tss_version(self):
        if "Torrent_Suite" not in self.version_data or not self.version_data['Torrent_Suite'].strip():
            self.logger.warning("TSS Version not in data")
            return None
        else:
            tss_version = unicode(self.version_data['Torrent_Suite'].strip())

            return tss_version

    '''
        Task: returns formatted start time of run
        @return    start_time:    start time of run
        @return    None:          data not found
    '''
    def get_start_time(self):
        if "Start Time" not in self.explog_data or not self.explog_data['Start Time'].strip():
            self.logger.warning("Start Time not in explog_data")
            return None
        else:
            start_time = unicode(self.explog_data['Start Time'].strip())
            '''sometimes the time is not in the standard format, so we adjust'''
            try:
                 start_time_obj = datetime.strptime(start_time, '%c')
            except ValueError:
                start_time_obj = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')

            start_time = start_time_obj

            return start_time

    '''
        Task: returns formatted end time of run
        @return    end_time:    end time of run
        @return    None:        data not found
    '''
    def get_end_time(self):
        if "End Time" not in self.explog_data or not self.explog_data['End Time'].strip():
            self.logger.warning("End Time not in explog_data")
            return None
        else:
            end_time = unicode(self.explog_data['End Time'].strip())
            '''sometimes the time is not in the standard format, so we adjust'''
            try:
                end_time_obj = datetime.strptime(end_time, '%c')
            except ValueError:
                end_time_obj = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

            end_time = end_time_obj

            return end_time

    '''
        Task: returns machine serial number
        @return    sn_number:    machine serial number
        @return    None:         data not found
    '''
    def get_sn_number(self):
        if 'Serial Number' not in self.explog_data or not self.explog_data['Serial Number'].strip():
            self.logger.warning("Serial Number not in data")
            return None
        else:
            sn_number = unicode(self.explog_data['Serial Number'].strip())

            return sn_number