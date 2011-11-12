import logging
import transaction
import datetime
import re
import unicodedata
import os
import os.path
from gnostic.models import DBSession
from gnostic.models import Archive
from gnostic.models import testers
from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.orm import subqueryload
import upload


def add_base_template(event):
    """Use layout.pt as a common frame for every other renderer."""
    layout = get_renderer("templates/layout.pt").implementation()
    event.update({"layout": layout})


@view_config(route_name="index", renderer="templates/index.pt")
def index(request):
    """Currently more of a static page.
    """
    return {}


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
    upload_root = request.registry.settings["technical_upload_root"]
    data = get_uploaded_file(request)
    label = unicode(request.POST["label"])
    folder = slugify(label)
    submitter_name = unicode(request.POST["submitter"])
    return submitter_name, label, upload_root, folder, data


@view_config(route_name="upload", renderer="templates/upload.pt")
def upload_file(request):
    """Receive the uploaded archive, create a folder to contain the diagnostic,
    save a copy of the archive to the folder, and extract it's contents there.
    This displays the extracted files relative paths and file sizes.
    """
    if "fileInput" in request.POST:
        submitter_name, label, upload_root, folder, data = make_report(request)
        destination = os.path.join(upload_root, folder)
        # if the user's label produces a destination path that already exists,
        # _derp the folder name until it's unique.
        while os.path.exists(destination):
            destination += "_derp"
        session = DBSession()
        archive = Archive(submitter_name, label, destination)
        archive.diagnostics = [t.diagnostic_record() for t in testers.values()]
        session.add(archive)
        session.flush()
        upload.queue_archive(request.registry.settings, archive.id, destination, data, testers)
        url = request.route_url('check', archive_id=archive.id)
        return HTTPFound(location=url)
    now = datetime.datetime.now()
    label = "Archive_%s" % now.strftime("%Y-%m-%d_%H-%M-%S")
    label = request.GET.get("label", label)
    name = ""
    name = request.GET.get("name", name)
    return {'label':label, 'name': name}


@view_config(route_name="check", renderer="templates/check.pt")
def check_archive(request):
    """Show the status of an archive given it's ID."""
    session = DBSession()
    archive_id = int(request.matchdict["archive_id"])
    archive = session.query(Archive).options(subqueryload(
        Archive.diagnostics)).filter(Archive.id==archive_id).first()
    session.close()
    return {"archive": archive}


@view_config(route_name="reports", renderer="templates/reports.pt")
def list_reports(request):
    session = DBSession()
    archives = session.query(Archive).all()
    return {"archives": archives}

@view_config(route_name="documentation", renderer="templates/documentation.pt")
def documentation(request):
    return {}