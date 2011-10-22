__author__ = 'bakennedy'

import io
import os
import os.path
import zipfile
from multiprocessing import Pool


result_pool = dict()


def list_zip_dirs(self, zip_file):
    """ Grabs all the directories in the zip structure
    This is necessary to create the structure before trying
    to extract the file to it.
    """
    return [n for n in zip_file.namelist() if name.endswith('/')]


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
    relative_files = [f[start:] for f in files]
    return prefix, relative_files


def validate_files(files):
    if any(os.path.isabs(d) for d in files):
        raise ValueError("Archive contains a mix of absolute and relative paths.")


def make_relative_directories(root, files):
    directories = [os.path.dirname(f) for f in files]
    for directory in directories:
        path = os.path.join(root, directory)
        if not os.path.exists(path):
            os.makedirs(path)


def unzip_archive(root, data):
    print("Zero")
    zip_file = zipfile.ZipFile(data, 'r')
    print("One")
    namelist = zip_file.namelist()
    print("One")
    prefix, files = get_common_prefix(namelist)
    print("One")
    validate_files(files)
    print("One")
    make_relative_directories(root, files)
    print("One")
    out_names = [(n, f) for n, f in zip(namelist, files) if
                                                    os.path.basename(f) != '']
    print("One")
    for key, out_name in out_names:
        if os.path.basename(out_name) != "":
            full_path = os.path.join(root, out_name)
            contents = zip_file.open(key, 'r')
            output_file = open(full_path, 'wb')
            output_file.write(contents.read())
            output_file.close()
    print("One")
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


def process_archive(destination, data):
    """Designed to run in a multiprocess external process, this unzips the
    file, writes it to disk inside a folder in which the zip file's contents
    are extracted.
    """
    # if the user's label produces a destination path that already exists,
    # _derp the folder name until it's unique.
    print("Starting")
    os.mkdir(destination)
    # Finally write the data to the output file
    output_file = open(os.path.join(destination, "archive.zip"), 'wb')
    data.seek(0)
    while 1:
        buffer = data.read(2 << 16)
        if not buffer:
            break
        output_file.write(buffer)
    output_file.close()
    data.seek(0)
    print("Unzipping")
    files = unzip_archive(destination, data)
    print("Unzipped!")
    file_info = [(f, sizer(destination, f)) for f in files]
    file_info.sort()
    print("Success!")
    return file_info


work_pool = Pool(2)

def queue_archive(label, destination, data):
    print("Queuing")
    serial = io.BytesIO()
    serial.write(data.read())
    async_out = work_pool.apply_async(process_archive, [destination, serial])
    result_pool[label] = async_out
    return async_out

