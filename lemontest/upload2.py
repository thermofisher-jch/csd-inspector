from beaker.container import logger
__author__ = 'bakennedy'

import json
import logging
import transaction
import os
import os.path
import tarfile
import zipfile
from celery.signals import worker_init
from celery.task import task
from celery.task import chord
from celery.utils.log import get_task_logger

from lemontest.models import DBSession
from lemontest.models import Archive
from lemontest.models import testers

from lemontest.models import MetricsPGM
from lemontest.models import MetricsProton
from lemontest.models import MetricsOTLog

from lemontest import diagnostic

from lemontest.metrics_pgm import *
from lemontest.metrics_proton import *
from lemontest.metrics_otlog import *

logger = logging.getLogger(__name__)

task_logger = get_task_logger(__name__)


class ZipArchive(zipfile.ZipFile):
    """A wrapper around the ZipFile class to present a simple
    uniform interface for inspecting and decompressing it's contents
    """
    def isfile(self, key):
        # Ack!? Is this true. Does zip have entries for non-files?
        # (directories/symlinks)
        return True


class TarArchive(object):
    """A wrapper around the TarFile class to present a simple
    uniform interface for inspecting and decompressing it's contents
    """
    
    def __init__(self, data):
        self.tar = tarfile.open(fileobj=data, mode='r')

    def open(self, key):
        return self.tar.extractfile(key)

    def namelist(self):
        return self.tar.getnames()

    def isfile(self, key):
        return self.tar.getmember(key).isfile()


@worker_init.connect
def initialize_session(signal, sender):
    from sqlalchemy import engine_from_config
    from celery import current_app
    worker_engine = engine_from_config(current_app.conf, 'sqlalchemy.')
    DBSession.configure(bind=worker_engine)


def get_common_prefix(files):
    """For a list of files, a common path prefix and a list file names with
    the prefix removed.

    Returns a tuple (prefix, relative_files):
        prefix: Longest common path to all files in the input. If input is a
                single file, contains full file directory.  Empty string is
                returned of there's no common prefix.
        relative_files: String containing the relative paths of files, skipping
                        the common prefix.
    """
    # Handle empty input
    if not files or not any(files):
        return '', []
    # find the common prefix in the directory names.
    directories = [os.path.dirname(f) for f in files]
    prefix = os.path.commonprefix(directories)
    start = len(prefix)
    if all(f[start] == "/" for f in files):
        start += 1
    relative_files = [f[start:] for f in files]
    return prefix, relative_files


def valid_files(files):
    black_list = [lambda f: "__MACOSX" in f]
    absolute_paths = [os.path.isabs(d) for d in files]
    if any(absolute_paths) and not all(absolute_paths):
        raise ValueError("Archive contains a mix of absolute and relative paths.")
    return [f for f in files if not any(reject(f) for reject in black_list)]


def make_relative_directories(root, files):
    directories = [os.path.dirname(f) for f in files]
    for directory in directories:
        path = os.path.join(root, directory)
        if not os.path.exists(path):
            os.makedirs(path)


def unzip_archive(root, archive_file):
    namelist = archive_file.namelist()
    namelist = valid_files(namelist)
    prefix, files = get_common_prefix(namelist)
    out_names = [(n, f) for n, f in zip(namelist, files) if
                                                    os.path.basename(f) != '']
    make_relative_directories(root, files)

    for key, out_name in out_names:
        if os.path.basename(out_name) != "":
            full_path = os.path.join(root, out_name)
            if not archive_file.isfile(key):
                continue
            contents = archive_file.open(key)
            if contents is None:
                continue
            try:
                output_file = open(full_path, 'wb')
                output_file.write(contents.read())
                output_file.close()
            except IOError as err:
                task_logger.error("For zip's file '%s', could not open '%s'" % (key, full_path))
                raise
    return [f for n, f in out_names]


suffixes = {
    'decimal': ('kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
    'binary': ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'),
    'gnu': "KMGTPEZY",
}

def natural_size(value, binary=False, gnu=False):
    """Format a number of byteslike a human readable filesize (eg. 10 kB).  By
    default, decimal suffixes (kB, MB) are used.  Passing binary=true will use
    binary suffixes (KiB, MiB) are used and the base will be 2**10 instead of
    10**3.  If ``gnu`` is True, the binary argument is ignored and GNU-style
    (ls -sh style) prefixes are used (K, M) with the 2**10 definition.
    Non-gnu modes are compatible with jinja2's ``filesizeformat`` filter."""
    if gnu: suffix = suffixes['gnu']
    elif binary: suffix = suffixes['binary']
    else: suffix = suffixes['decimal']

    base = 1024 if (gnu or binary) else 1000
    bytes = float(value)

    if bytes == 1 and not gnu: return '1 Byte'
    elif bytes < base and not gnu: return '%d Bytes' % bytes
    elif bytes < base and gnu: return '%dB' % bytes

    for i, s in enumerate(suffix):
        unit = base ** (i + 2)
        if bytes < unit and not gnu:
            return '%.1f %s' % ((base * bytes / unit), s)
        elif bytes < unit and gnu:
            return '%.1f%s' % ((base * bytes / unit), s)
    if gnu:
        return '%.1f%s' % ((base * bytes / unit), s)
    return '%.1f %s' % ((base * bytes / unit), s)


def sizer(destination, target):
    full_path = os.path.join(destination, target)
    return natural_size(os.stat(full_path).st_size, gnu=True)


def get_diagnostics(archive_type):
    return [t.diagnostic_record() for t in testers[archive_type].values()]


def make_diagnostic_jobs(archive, testers):
    testers2 = dict()
    with open("/opt/inspector/inspector/lemontest/test_manifest.json") as manifest_file2:
        tests2 = json.load(manifest_file2)
    testers2.update(diagnostic.get_testers(tests2, "/opt/inspector/inspector/lemontest/diagnostics"))
    return [diagnostic.run_tester.subtask(
                    (testers2[archive.archive_type][d.name], d.id, archive.path))
                    for d in archive.diagnostics]


def run_diagnostics(archive_id, jobs):
    if jobs:
        callback = finalize_report.subtask((archive_id,))
        chord(jobs)(callback)
    else:
        finalize_report.delay(None, archive_id)


def unzip_csa(archive):
    try:
        full_path = os.path.join(archive.path, "archive.zip")
        os.rename(os.path.join(archive.path, "uploaded_file.tmp"), full_path)
        if zipfile.is_zipfile(full_path):
            archive_file = ZipArchive(open(full_path, 'rb'))
            unzip_archive(archive.path, archive_file)
            return True
        else:
            archive.status = u"Error, archive is not a zip"
    except IOError as err:
        archive.status = u"Error during archive unzip"
        task_logger.error("Archive {0} had an IOError: {1}".format(archive.id, err))
    except zipfile.BadZipfile as err:
        archive.status = u'Error in archive zip, "%s"' % err
        task_logger.error("Archive {0} had a bad zip file: {1}".format(archive.id, err))
    return False 


def untar_upload(archive):
    try:
        full_path = os.path.join(archive.path, "logs.tar")
        os.rename(os.path.join(archive.path, "uploaded_file.tmp"), full_path)
        if tarfile.is_tarfile(full_path):
            archive_file = TarArchive(open(full_path, 'rb'))
            unzip_archive(archive.path, archive_file)
            return True
        else:
            archive.status = u"Error, archive is not a tar file"
    except IOError as err:
        archive.status = u"Error during archive untar"
        task_logger.error("Archive {0} had an IOError: {1}".format(archive.id, err))
    except tarfile.TarError as err:
        archive.status = u'Error in archive tar file, "%s"' % err
        task_logger.error("Archive {0} had a bad tar file: {1}".format(archive.id, err))
    return False 


def one_touch_log(archive):
    full_path = os.path.join(archive.path, "onetouch.log")
    os.rename(os.path.join(archive.path, "uploaded_file.tmp"), full_path)
    return True


archive_handlers = {
    "PGM_Run": unzip_csa,
    "Proton": unzip_csa,
    "OT_Log": one_touch_log,
    "Ion_Chef": untar_upload,
}


def handle_archive(archive):
    return archive_handlers[archive.archive_type](archive)


@task
def process_archive(archive_id, upload_name, testers):
    """This is an external, celery task which unzips the file, restructures
    it's into a folder hierarchy relative to destination, and writes the
    archive's contents into that restructured hierarchy.
    """
    from lemontest.metrics_migration import metrics_migration
    logger = task_logger
    archive = DBSession.query(Archive).get(archive_id)
    logger.info("Processing archive in %s" % archive.path)
    if archive is None:
        logger.error("Archive id = %s not found." % archive_id)
        return
    try:
        temp_file = os.path.join(archive.path, "uploaded_file.tmp")
        if os.path.exists(temp_file):
            if handle_archive(archive):
                archive.status = u"Starting tests"
                archive.diagnostics = get_diagnostics(archive.archive_type)
                transaction.commit()
                jobs = make_diagnostic_jobs(archive, testers)
                run_diagnostics(archive_id, jobs)

                metrics_migration.delay(archive_id)
            else:
                raise Exception("Could not process upload_file.tmp")

        '''
        if archive.archive_type == "Ion Chef":
            pass
        '''

    except Exception as err:
        archive = DBSession.query(Archive).get(archive_id)
        archive.status = u"Error processing archive"
        task_logger.exception("Archive {} failed with an error".format(archive_id))
    transaction.commit()

'''
    Task: create/initialize objects needed to parse all pgm metrics,
          check if the files needed were found,
          set metric data for each data point for that metric type,
          commit all pending DB transactions
    @author: Anthony Rodriguez
'''
@task
def set_metrics_pgm(metrics_pgm_id):
    metric = DBSession.query(MetricsPGM).get(metrics_pgm_id)

    bfmask_stats = pgm_bfmask_stats.Metrics_PGM_Bfmask_Stats(metric.archive.path, logger)
    basecaller_json = pgm_basecaller_json.Metrics_PGM_BaseCaller_JSON(metric.archive.path, logger)
    datasets_basecaller_json = pgm_datasets_basecaller_json.Metrics_PGM_Datasets_BaseCaller_JSON(metric.archive.path, logger)
    explog = pgm_explog.Metrics_PGM_Explog(metric.archive.path, logger)
    initlog = pgm_initlog.Metrics_PGM_InitLog(metric.archive.path, logger)
    quality_summary = pgm_quality_summary.Metrics_PGM_Quality_Summary(metric.archive.path, logger)
    tfstats_json = pgm_tfstats_json.Metrics_PGM_TFStats_JSON(metric.archive.path, logger)

    if bfmask_stats.is_valid():
        metric.isp_wells = bfmask_stats.get_isp_wells()
        metric.live_wells = bfmask_stats.get_live_wells()
        metric.library_wells = bfmask_stats.get_library_wells()
        metric.isp_loading = bfmask_stats.get_isp_loading()
        metric.test_fragment = bfmask_stats.get_test_fragment()

    if basecaller_json.is_valid():
        metric.polyclonal = basecaller_json.get_polyclonal()
        metric.polyclonal_pct = basecaller_json.get_polyclonal_pct(metric.library_wells)
        metric.primer_dimer = basecaller_json.get_primer_dimer()
        metric.primer_dimer_pct = basecaller_json.get_primer_dimer_pct(metric.library_wells)
        metric.low_quality = basecaller_json.get_low_quality()
        metric.low_quality_pct = basecaller_json.get_low_quality_pct(metric.library_wells)
        metric.usable_reads = basecaller_json.get_usable_reads()
        metric.usable_reads_pct = basecaller_json.get_usable_reads_pct(metric.library_wells)

    if datasets_basecaller_json.is_valid():
        metric.barcode_set = datasets_basecaller_json.get_barcode_set()

    if explog.is_explog_valid():
        metric.pgm_temperature = explog.get_pgm_temperature()
        metric.pgm_pressure = explog.get_pgm_pressure()
        metric.chip_temperature = explog.get_chip_temperature()
        metric.chip_noise = explog.get_chip_noise()
        metric.gain = explog.get_gain()
        metric.cycles = explog.get_cycles()
        metric.flows = explog.get_flows()
        metric.chip_type = explog.get_chip_type()
        metric.run_type = explog.get_run_type()
        metric.reference = explog.get_reference()
        metric.seq_kit = explog.get_seq_kit()
        metric.seq_kit_lot = explog.get_seq_kit_lot()
        metric.sw_version = explog.get_sw_version()
        metric.hw_version = explog.get_hw_version()
        metric.start_time = explog.get_start_time()
        metric.end_time = explog.get_end_time()
        metric.sn_number = explog.get_sn_number()

    if explog.is_version_valid():
        metric.tss_version = explog.get_tss_version()

    if initlog.is_initlog_valid():
        metric.start_ph = initlog.get_start_ph()
        metric.end_ph = initlog.get_end_ph()
        metric.w1_added = initlog.get_w1_added()

    if initlog.is_basecaller_valid():
        metric.num_barcodes = initlog.get_num_barcodes()

    if tfstats_json.is_valid():
        metric.tf_50q17_pct = tfstats_json.get_tf_50Q17_pct()

    if quality_summary.is_valid():
        metric.system_snr = quality_summary.get_system_snr()
        metric.total_bases = quality_summary.get_total_bases()
        metric.mean_read_length = quality_summary.get_mean_read_length()
        metric.total_reads = quality_summary.get_total_reads()

    transaction.commit()

'''
    Task: create/initialize objects needed to parse all proton metrics,
          check if the files needed were found,
          set metric data for each data point for that metric type,
          commit all pending DB transactions
    @author: Anthony Rodriguez
'''
@task
def set_metrics_proton(metrics_proton_id):
    metric = DBSession.query(MetricsProton).get(metrics_proton_id)

    bfmask_stats = proton_bfmask_stats.Metrics_Proton_Bfmask_Stats(metric.archive.path, logger)
    basecaller_json = proton_basecaller_json.Metrics_Proton_BaseCaller_JSON(metric.archive.path, logger)
    explog = proton_explog.Metrics_Proton_Explog(metric.archive.path, logger)
    initlog = proton_initlog.Metrics_Proton_InitLog(metric.archive.path, logger)
    quality_summary = proton_quality_summary.Metrics_Proton_Quality_Summary(metric.archive.path, logger)
    tfstats_json = proton_tfstats_json.Metrics_Proton_TFStats_JSON(metric.archive.path, logger)

    if bfmask_stats.is_valid():
        metric.isp_wells = bfmask_stats.get_isp_wells()
        metric.live_wells = bfmask_stats.get_live_wells()
        metric.library_wells = bfmask_stats.get_library_wells()
        metric.isp_loading = bfmask_stats.get_isp_loading()
        metric.test_fragment = bfmask_stats.get_test_fragment()

    if basecaller_json.is_valid():
        metric.polyclonal = basecaller_json.get_polyclonal()
        metric.polyclonal_pct = basecaller_json.get_polyclonal_pct(metric.library_wells)
        metric.primer_dimer = basecaller_json.get_primer_dimer()
        metric.primer_dimer_pct = basecaller_json.get_primer_dimer_pct(metric.library_wells)
        metric.low_quality = basecaller_json.get_low_quality()
        metric.low_quality_pct = basecaller_json.get_low_quality_pct(metric.library_wells)
        metric.usable_reads = basecaller_json.get_usable_reads()
        metric.usable_reads_pct = basecaller_json.get_usable_reads_pct(metric.library_wells)

    if explog.is_explog_valid():
        metric.proton_temperature = explog.get_proton_temperature()
        metric.proton_pressure = explog.get_proton_pressure()
        metric.target_pressure = explog.get_target_pressure()
        metric.chip_temperature = explog.get_chip_temperature()
        metric.chip_noise = explog.get_chip_noise()
        metric.gain = explog.get_gain()
        metric.cycles = explog.get_cycles()
        metric.flows = explog.get_flows()
        metric.chip_type = explog.get_chip_type()
        metric.run_type = explog.get_run_type()
        metric.reference = explog.get_reference()
        metric.seq_kit = explog.get_seq_kit()
        metric.seq_kit_lot = explog.get_seq_kit_lot()
        metric.sw_version = explog.get_sw_version()
        metric.start_time = explog.get_start_time()
        metric.end_time = explog.get_end_time()
        metric.barcode_set = explog.get_barcode_set()
        metric.sn_number = explog.get_sn_number()
        metric.scripts_version = explog.get_scripts_version()

    if explog.is_version_valid():
        metric.tss_version = explog.get_tss_version()

    if initlog.is_initlog_valid():
        metric.start_ph = initlog.get_start_ph()
        metric.end_ph = initlog.get_end_ph()
        metric.w1_added = initlog.get_w1_added()

    if initlog.is_basecaller_valid():
        metric.num_barcodes = initlog.get_num_barcodes()

    if tfstats_json.is_valid():\
        metric.tf_50q17_pct = tfstats_json.get_tf_50Q17_pct()

    if quality_summary.is_valid():
        metric.system_snr = quality_summary.get_system_snr()
        metric.total_bases = quality_summary.get_total_bases()
        metric.mean_read_length = quality_summary.get_mean_read_length()
        metric.total_reads = quality_summary.get_total_reads()

    transaction.commit()

'''
    Task: create/initialize objects needed to parse all otlog metrics,
          check if the files needed were found,
          set metric data for each data point for that metric type,
          commit all pending DB transactions
    @author: Anthony Rodriguez
'''
@task
def set_metrics_otlog(metrics_otlog_id):
    metric = DBSession.query(MetricsOTLog).get(metrics_otlog_id)

    otlog_parser = otlog.OTLog(metric.archive.path, logger)

    if otlog_parser.is_valid():
        metric.ambient_temp_high = otlog_parser.get_ambient_temp_high()
        metric.ambient_temp_low = otlog_parser.get_ambient_temp_low()
        metric.internal_case_temp_high = otlog_parser.get_internal_case_temp_high()
        metric.internal_case_temp_low = otlog_parser.get_internal_case_temp_low()
        metric.pressure_high = otlog_parser.get_pressure_high()
        metric.pressure_low = otlog_parser.get_pressure_low()
        metric.ot_version = otlog_parser.get_ot_version()
        metric.sample_inject_abort = otlog_parser.get_sample_inject_abort()
        metric.oil_pump_status = otlog_parser.get_oil_pump_status()
        metric.sample_pump_status = otlog_parser.get_sample_pump_status()
        metric.run_time = otlog_parser.get_run_time()

    transaction.commit()

@task
def finalize_report(results, archive_id):
    logger = task_logger
    archive = DBSession.query(Archive).get(archive_id)
    archive.status = u"Diagnostics completed."
    transaction.commit()
    logger.info("Finished applying jobs.")


def queue_archive(archive_id, archive_path, data, testers):
    os.mkdir(archive_path)
    os.mkdir(os.path.join(archive_path, "test_results"))
    data.seek(0)
    with open(os.path.join(archive_path, "uploaded_file.tmp"), 'wb') as output_file:
        buffer = data.read(2 << 16)
        while buffer:
            output_file.write(buffer)
            buffer = data.read(2 << 16)
    return process_archive.delay(archive_id, "uploaded_file.tmp", testers)
