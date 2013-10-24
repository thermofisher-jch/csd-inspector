__author__ = 'bakennedy'

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
from lemontest import diagnostic

logger = logging.getLogger(__name__)

task_logger = get_task_logger(__name__)

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


def unzip_archive(root, data):
    zip_file = zipfile.ZipFile(data, 'r')
    namelist = zip_file.namelist()
    namelist = valid_files(namelist)
    prefix, files = get_common_prefix(namelist)
    make_relative_directories(root, files)
    out_names = [(n, f) for n, f in zip(namelist, files) if
                                                    os.path.basename(f) != '']
    for key, out_name in out_names:
        if os.path.basename(out_name) != "":
            full_path = os.path.join(root, out_name)
            contents = zip_file.open(key, 'r')
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

    for i,s in enumerate(suffix):
        unit = base ** (i+2)
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
    return [diagnostic.run_tester.subtask(
                    (testers[archive.archive_type][d.name], d.id, archive.path))
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
            archive_file = open(full_path, 'rb')
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
            with tarfile.TarFile(full_path) as tar:
                tar.extractall(archive.path)
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


@task
def process_archive(archive_id, upload_name, testers):
    """This is an external, celery task which unzips the file, restructures
    it's into a folder hierarchy relative to destination, and writes the
    archive's contents into that restructured hierarchy.
    """
    logger = task_logger
    archive = DBSession.query(Archive).get(archive_id)
    logger.info("Processing archive in %s" % archive.path)
    if archive is None:
        logger.error("Archive id = %s not found." % archive_id)
        return
    try:
        if archive_handlers[archive.archive_type](archive):
            archive.status = u"Starting tests"
            archive.diagnostics = get_diagnostics(archive.archive_type)
            transaction.commit()
            jobs = make_diagnostic_jobs(archive, testers)
            run_diagnostics(archive_id, jobs)
    except Exception as err:
        archive = DBSession.query(Archive).get(archive_id)
        archive.status = u"Error processing archive"
        task_logger.exception("Archive {} failed with an error".format(archive_id))
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
