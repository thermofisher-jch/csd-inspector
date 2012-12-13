import logging
import transaction
import datetime
import re
import unicodedata
import mimetypes
import os
import shutil
import os.path
from lemontest.models import DBSession
from lemontest.models import Archive
from lemontest.models import Diagnostic
from lemontest.models import testers
from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.response import Response
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


def get_diagnostics(archive_type):
    return [t.diagnostic_record() for t in testers[archive_type].values()]


def make_archive(request):
    """Do everything needed to make a new Archive"""
    label = unicode(request.POST["label"])
    site = unicode(request.POST["site"])
    archive_type = unicode(request.POST["archive_type"])
    submitter_name = unicode(request.POST["submitter"])

    upload_root = request.registry.settings["upload_root"]
    folder = slugify(label)
    destination = os.path.join(upload_root, folder)
    # if the user's label produces a destination path that already exists,
    # _derp the folder name until it's unique.
    while os.path.exists(destination):
        destination += "_derp"

    archive = Archive(submitter_name, label, site, archive_type, destination)
    archive.diagnostics = get_diagnostics(archive_type)

    return archive


@view_config(route_name="upload", renderer="templates/upload.pt")
def upload_file(request):
    """Receive the uploaded archive, create a folder to contain the diagnostic,
    save a copy of the archive to the folder, and extract it's contents there.
    This displays the extracted files relative paths and file sizes.
    """
    if "fileInput" in request.POST:
        archive = make_archive(request)
        data = get_uploaded_file(request)
        DBSession.add(archive)
        DBSession.flush()
        upload.queue_archive(request.registry.settings, archive.id, archive.path, data, testers)
        url = request.route_url('check', archive_id=archive.id)
        return HTTPFound(location=url)
    now = datetime.datetime.now()
    label = "Archive_%s" % now.strftime("%Y-%m-%d_%H-%M-%S")
    label = request.GET.get("label", label)
    name = ""
    name = request.GET.get("name", name)
    print(testers.keys())
    return {'label':label, 'name': name, 'archive_types': testers.keys()}


@view_config(route_name="check", renderer="templates/check.pt")
def check_archive(request):
    """Show the status of an archive given it's ID."""
    session = DBSession()
    archive_id = int(request.matchdict["archive_id"])
    archive = session.query(Archive).options(subqueryload(
        Archive.diagnostics)).filter(Archive.id==archive_id).first()
    session.close()
    archive.diagnostics.sort(key=lambda x: -int(x.priority))
    for test in archive.diagnostics:
        test.readme = testers[archive.archive_type][test.name].readme
    basename = os.path.basename(archive.path)
    return {"archive": archive, "basename": basename}


@view_config(route_name="super_delete")
def super_delete(request):
    archive_id = int(request.matchdict["archive_id"])
    archive = DBSession.query(Archive).options(subqueryload(
        Archive.diagnostics)).filter(Archive.id==archive_id).first()
    for diagnostic in archive.diagnostics:
        out = diagnostic.get_output_path()
        if os.path.exists(out):
            shutil.rmtree(out)
    if os.path.exists(archive.path):
        shutil.rmtree(archive.path)
    DBSession.delete(archive)
    url = request.route_url('reports')
    return HTTPFound(location=url)


@view_config(route_name="rerun")
def rerun_archive(request):
    archive_id = int(request.matchdict["archive_id"])
    archive = DBSession.query(Archive).options(subqueryload(
        Archive.diagnostics)).filter(Archive.id==archive_id).first()
    for diagnostic in archive.diagnostics:
        out = diagnostic.get_output_path()
        if os.path.exists(out):
            shutil.rmtree(out)
        DBSession.delete(diagnostic)
    archive.diagnostics = get_diagnostics(archive.archive_type)
    DBSession.flush()
    upload.run_diagnostics(archive, request.registry.settings, testers)
    url = request.route_url('check', archive_id=archive_id)
    return HTTPFound(location=url)


@view_config(route_name="reports", renderer="templates/reports.pt")
def list_reports(request):
    archives = DBSession.query(Archive).order_by(Archive.time.desc()).all()
    return {"archives": archives}


@view_config(route_name="documentation", renderer="templates/documentation.pt")
def documentation(request):
    return {}


@view_config(route_name="test_readme")
def test_readme(request):
    test_name = request.matchdict["test_name"]
    for archive_type in testers.keys():
        readme = test_name in testers[archive_type] and testers[archive_type][test_name].readme
    if readme is not None:
        mime = mimetypes.guess_type(readme)[0] or 'text/plain'
        response = Response(content_type=mime)
        response.app_iter = open(readme, 'rt')
    else:
        response = HTTPFound("%s does not have a README file." % test_name)
    return response
