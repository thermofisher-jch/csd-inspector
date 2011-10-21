import datetime
import re
import unicodedata
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


@view_config(route_name="upload", renderer="templates/upload.pt")
def upload(request):
    upload_root = request.registry.settings["upload_root"]
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
    size = os.stat(output_name).st_size
    return {"archive_path": destination, "archive_size": size}