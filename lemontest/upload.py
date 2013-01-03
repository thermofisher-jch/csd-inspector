__author__ = 'bakennedy'

import logging
import transaction
import os
import os.path
import zipfile
from celery.task import task
from celery.task import chord

from sqlalchemy import engine_from_config

from lemontest.models import DBSession
from lemontest.models import Archive
from lemontest.models import initialize_sql
from lemontest import diagnostic

logger = logging.getLogger(__name__)


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


def unzip_archive(root, data, logger):
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
                logger.error("For zip's file '%s', could not open '%s'" % (key, full_path))
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


def run_diagnostics(archive, settings, testers):
    jobs = [diagnostic.run_tester.subtask(
                    (testers[archive.archive_type][d.name], settings, d.id, archive.path))
                    for d in archive.diagnostics]
    if jobs:
        callback = finalize_report.subtask((settings, archive.id))
        chord(jobs)(callback)
    else:
        finalize_report.delay(None, settings, archive.id)


@task
def process_archive(settings, archive_id, destination, archive_name, testers):
    """This is an external, celery task which unzips the file, restructures
    it's into a folder hierarchy relative to destination, and writes the
    archive's contents into that restructured hierarchy.
    """
    logger = process_archive.get_logger()
    logger.info("Processing archive in %s" % destination)
    engine = engine_from_config(settings)
    initialize_sql(engine)
    # Finally read the data from the uploaded zip file
    session = DBSession()
    archive = session.query(Archive).get(archive_id)
    try:
        archive_file = open(os.path.join(destination, archive_name), 'rb')
        unzip_archive(destination, archive_file, logger)
        logger.info("Archive is %s" % str(archive))
        archive.status = u"Archive decompressed successfully. Starting diagnostics."
        os.mkdir(os.path.join(archive.path, "test_results"))
        run_diagnostics(archive, settings, testers)
    except IOError as err:
        archive.status = "Failed during archive extraction"
    transaction.commit()


@task
def finalize_report(results, settings, archive_id):
    logger = finalize_report.get_logger()
    engine = engine_from_config(settings)
    initialize_sql(engine)
    session = DBSession()
    archive = session.query(Archive).get(archive_id)
    archive.status = u"Diagnostics completed."
    transaction.commit()
    logger.info("Finished applying jobs.")


def queue_archive(settings, archive_id, destination, data, testers):
    os.mkdir(destination)
    output_file = open(os.path.join(destination, "archive.zip"), 'wb')
    data.seek(0)
    while 1:
        buffer = data.read(2 << 16)
        if not buffer:
            break
        output_file.write(buffer)
    output_file.close()
    return process_archive.delay(settings, archive_id, destination, "archive.zip", testers)
