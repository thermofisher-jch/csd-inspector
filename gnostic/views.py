import datetime
import re
import unicodedata
import zipfile
import os
import os.path
from gnostic.models import DBSession
from gnostic.models import MyModel
from pyramid.view import view_config


@view_config(route_name="index", renderer="templates/index.pt")
def index(request):
    #dbsession = DBSession()
    #root = dbsession.query(MyModel).filter(MyModel.name==u'root').first()
    now = datetime.datetime.now()
    label = now.strftime("%Y-%m-%d_%H-%M-%S")
    return {'label':label}


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.  Slightly modified from the Django source
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)


def get_uploaded_file(request):
    data = request.POST["fileInput"].file
    return data


def make_report(request):
    data = get_uploaded_file(request)
    label = request.POST["label"]
    folder = slugify(label)
    return label, folder, data


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
    zip_file = zipfile.ZipFile(data, 'r')
    namelist = zip_file.namelist()
    prefix, files = get_common_prefix(namelist)
    validate_files(files)
    make_relative_directories(root, files)
    out_names = [(n, f) for n, f in zip(namelist, files) if
                                                    os.path.basename(f) != '']
    for key, out_name in out_names:
        if os.path.basename(out_name) != "":
            full_path = os.path.join(root, out_name)
            contents = zip_file.open(key, 'r')
            output_file = open(full_path, 'wb')
            output_file.write(contents.read())
            output_file.close()
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


@view_config(route_name="upload", renderer="templates/upload.pt")
def upload(request):
    """Receive the uploaded archive, create a folder to contain the diagnostic,
    save a copy of the archive to the folder, and extract it's contents there.
    This displays the extracted files relative paths and file sizes.
    """
    upload_type = request.matchdict["type"]
    if upload_type == "technical":
        upload_root = request.registry.settings["technical_upload_root"]
    elif upload_type == "experimental":
        upload_root = request.registry.settings["experimental_upload_root"]
    label, folder, data = make_report(request)
    destination = os.path.join(upload_root, folder)
    # if the user's label produces a destination path that already exists,
    # _derp the folder name until it's unique.
    while os.path.exists(destination):
        destination += "_derp"
    os.mkdir(destination)
    # Finally write the data to the output file
    output_name = os.path.join(destination, "archive.zip")
    output_file = open(output_name, 'wb')
    data.seek(0)
    while 1:
        buffer = data.read(2 << 16)
        if not buffer:
            break
        output_file.write(buffer)
    output_file.close()
    data.seek(0)
    files = unzip_archive(destination, data)
    def sizer(target):
        full_path = os.path.join(destination, target)
        return natural_size(os.stat(full_path).st_size, gnu=True)
    file_info = [(f, sizer(f)) for f in files]
    file_info.sort()
    return {"archive_path": destination, "archive_contents": file_info}