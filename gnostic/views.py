import datetime
import re
import unicodedata
import os
import os.path
from gnostic.models import DBSession
from gnostic.models import MyModel
from pyramid.view import view_config
import upload


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
    """Do everything for which the request object is needed."""
    if request.matchdict["type"] == "technical":
        upload_root = request.registry.settings["technical_upload_root"]
    else:
        upload_root = request.registry.settings["experimental_upload_root"]
    data = get_uploaded_file(request)
    label = request.POST["label"]
    folder = slugify(label)
    return label, upload_root, folder, data


@view_config(route_name="upload", renderer="templates/upload.pt")
def upload_file(request):
    """Receive the uploaded archive, create a folder to contain the diagnostic,
    save a copy of the archive to the folder, and extract it's contents there.
    This displays the extracted files relative paths and file sizes.
    """
    label, upload_root, folder, data = make_report(request)
    destination = os.path.join(upload_root, folder)
    while os.path.exists(destination):
        destination += "_derp"
    upload.queue_archive(label, destination, data)
    print("Returned!")
    return {"archive_path": destination, "folder": folder, "label": label}