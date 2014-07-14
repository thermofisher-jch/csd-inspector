import logging
import transaction
import re
import unicodedata
import mimetypes
import os
import shutil
import os.path
from datetime import datetime

from lemontest.models import MetricsPGM

from lemontest.models import DBSession
from lemontest.models import Archive
from lemontest.models import Diagnostic
from lemontest.models import Tag
from lemontest.models import testers
from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.exceptions import NotFound
from sqlalchemy.orm import subqueryload
from webhelpers import paginate
import upload
import helpers

from lemontest.csv_support import make_csv

logger = logging.getLogger(__name__)

status_highlights = {
    "Alert": "important",
    "Warning": "warning",
    "Info": "info",
    "OK": "success"
}

archive_type_files = {
    "PGM_Run": "archive.zip",
    "Proton": "archive.zip",
    "Ion_Chef": "logs.tar",
    "OT_Log": "onetouch.log"
}

def add_helpers(event):
    event['h'] = helpers


@view_config(route_name="index", renderer="index.mako",
    permission='view')
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


def make_archive(request):
    """Do everything needed to make a new Archive"""
    label = unicode(request.POST["label"] or "Archive_%s" % datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    site = unicode(request.POST["site"])
    archive_type = unicode(request.POST["archive_type"])
    submitter_name = unicode(request.POST["name"])

    archive = Archive(submitter_name, label, site, archive_type)

    return archive


def upload_validate(data):
    return hasattr(data.get('fileInput', None), 'file')


def post_upload_validate(request):
    if request.method == "POST" and upload_validate(request.POST):
        for param in ['name', 'site', 'archive_type']:
            request.session['upload.' + param] = request.POST.get(param, '')
        request.session.save()
        upload_root = request.registry.settings["upload_root"]
        archive = make_archive(request)
        data = get_uploaded_file(request)
        DBSession.add(archive)
        DBSession.flush()
        archive.path = os.path.join(upload_root, unicode(archive.id))
        archive_id = archive.id
        archive_path = archive.path
        transaction.commit()
        upload.queue_archive(archive_id, archive_path, data, testers)
        url = request.route_url('check', archive_id=archive_id)
        return True, url
    return False, None


@view_config(route_name="upload", xhr=True, renderer="json",
    permission='view')
def xhr_upload_file(request):
    valid, url = post_upload_validate(request)
    return {"valid": valid, "url": url}


@view_config(route_name="upload", xhr=False, renderer="upload.mako",
    permission='view')
def upload_file(request):
    """Receive the uploaded archive, create a folder to contain the diagnostic,
    save a copy of the archive to the folder, and extract it's contents there.
    This displays the extracted files relative paths and file sizes.
    """
    ctx = {
        'label':request.GET.get("label", ""),
        'name': request.GET.get("name", "") or request.session.get("upload.name", ""),
        'site': request.session.get("upload.site", ""),
        'archive_types': testers.keys(),
        'archive_type': request.session.get("upload.archive_type", None),
    }
    if request.method == "POST":
        ctx['label'] = request.POST.get("label", "")
        ctx['name'] = request.POST.get("name", "")
        ctx['archive_type'] = request.POST.get("archive_type", "")
        ctx['site'] = request.POST.get("site", "")
        if upload_validate(request.POST):
            upload_root = request.registry.settings["upload_root"]
            archive = make_archive(request)
            data = get_uploaded_file(request)
            DBSession.add(archive)
            DBSession.flush()
            archive.path = os.path.join(upload_root, unicode(archive.id))
            archive_id = archive.id
            archive_path = archive.path
            transaction.commit()
            upload.queue_archive(archive_id, archive_path, data, testers)
            url = request.route_url('check', archive_id=archive_id)
            return HTTPFound(location=url)
    return ctx


def parse_tags(tag_string):
    tags = []
    for name in tag_string.lower().split():
        name = name.strip()
        if name:
            tag = DBSession.query(Tag).filter(Tag.name == name).first()
            if tag is None:
                tag = Tag(name=name)
                DBSession.add(tag)
            tags.append(tag)
    return tags


@view_config(route_name="check", renderer="check.mako",
    permission='view')
def check_archive(request):
    """Show the status of an archive given it's ID."""
    archive_id = int(request.matchdict["archive_id"])
    archive = DBSession.query(Archive).options(subqueryload(
        Archive.diagnostics)).filter(Archive.id == archive_id).first()
    if not archive:
        raise NotFound()
    if request.POST:
        archive.label = request.POST['label']
        archive.site = request.POST['site']
        archive.archive_type = request.POST['archive_type']
        archive.summary = request.POST['summary']
        archive.tags = parse_tags(request.POST['tags'])
        DBSession.flush()
        return HTTPFound(location=request.current_route_url())
    for test in archive.diagnostics:
        test.get_readme_path()
    basename = os.path.basename(archive.path)
    return {"archive": archive, "basename": basename, 'archive_types': testers.keys(),
        "status_highlights": status_highlights, "tag_string": " ".join(t.name for t in archive.tags),
        "download_file": archive_type_files.get(archive.archive_type, "")}


@view_config(route_name="super_delete", request_method="POST",
    permission='view')
def super_delete(request):
    archive_id = int(request.matchdict["archive_id"])
    archive = DBSession.query(Archive).options(subqueryload(
        Archive.diagnostics)).filter(Archive.id == archive_id).first()
    for diagnostic in archive.diagnostics:
        out = diagnostic.get_output_path()
        if os.path.exists(out):
            shutil.rmtree(out)
    if os.path.exists(archive.path):
        shutil.rmtree(archive.path)
    DBSession.delete(archive)
    url = request.route_url('reports')
    return HTTPFound(location=url)


@view_config(route_name="rerun", request_method="POST", permission='view')
def rerun_archive(request):
    archive_id = int(request.matchdict["archive_id"])
    archive = DBSession.query(Archive).options(subqueryload(
        Archive.diagnostics)).filter(Archive.id == archive_id).first()
    for diagnostic in archive.diagnostics:
        out = diagnostic.get_output_path()
        if os.path.exists(out):
            shutil.rmtree(out)
        DBSession.delete(diagnostic)
    archive.diagnostics = upload.get_diagnostics(archive.archive_type)
    DBSession.flush()
    jobs = upload.make_diagnostic_jobs(archive, testers)
    transaction.commit()
    upload.run_diagnostics(archive_id, jobs)
    url = request.route_url('check', archive_id=archive_id)
    return HTTPFound(location=url)


def clean_strings(params):
    for key, value in params.items():
        params[key] = value.strip()
    return params


@view_config(route_name="reports", renderer="reports.mako",
    permission='view')
def list_reports(request):
    search_params = clean_strings({
        'archive_type': request.params.get('archive_type', u''),
        'submitter_name': request.params.get('submitter_name', u''),
        'site': request.params.get('site', u''),
        'label': request.params.get('label', u''),
        'summary': request.params.get('summary', u''),
    })
    page = int(request.params.get("page", 1))
    page_url = paginate.PageURL_WebOb(request)
    archive_query = DBSession.query(Archive).order_by(Archive.time.desc())
    is_search = False
    for column, value in search_params.items():
        if value:
            is_search = True
            if column == 'archive_type':
                archive_query = archive_query.filter(Archive.archive_type == value)
            else:
                archive_query = archive_query.filter(getattr(Archive, column).ilike(u"%{}%".format(value)))
    archives = paginate.Page(archive_query, page, items_per_page=100, url=page_url)
    pages = [archives.first_page]
    left_pagius = 5
    right_pagius = 5
    total = 2 + left_pagius + 1 + right_pagius + 2
    if archives.page_count <= total:
        pages = range(1, archives.page_count + 1)
    else:
        if archives.page - left_pagius < 3:
            diff = 3 - (archives.page - left_pagius)
            right_pagius += diff
            left_pagius = max(left_pagius - diff, 0)
        if archives.page + right_pagius > archives.page_count - 2:
            diff = (archives.page + right_pagius + 1) - (archives.page_count - 1)
            left_pagius += diff
            right_pagius = max(right_pagius - diff, 0)
        if archives.page - left_pagius > 3:
            pages.append("..")
        elif archives.page - left_pagius == 3:
            pages.append("2")

        if archives.page > 2:
            pages.extend(range(max(archives.page - left_pagius, 3), archives.page))
        if archives.page >= 2:
            pages.append(archives.page)

        pages.extend(range(archives.page + 1, min(archives.page + right_pagius + 1, archives.page_count)))

        if archives.page + right_pagius < archives.page_count - 2:
            pages.append("..")
        elif archives.page + right_pagius == archives.page_count - 2:
            pages.append(archives.page_count - 1)

        if archives.page < archives.page_count:
            pages.append(archives.page_count)

    return {'archives': archives, 'pages': pages, 'page_url': page_url, 'is_search': is_search,
            'archive_types': testers.keys(), 'search': search_params}


@view_config(route_name="documentation", renderer="documentation.mako",
    permission='view')
def documentation(request):
    return {}


@view_config(route_name="test_readme",
    permission='view')
def test_readme(request):
    test_name = request.matchdict["test_name"]
    readme = None
    for archive_type in testers.keys():
        if test_name in testers[archive_type]:
            readme = testers[archive_type][test_name].readme
            break
    if readme:
        mime = mimetypes.guess_type(readme)[0] or 'text/plain'
        response = Response(content_type=mime)
        response.app_iter = open(readme, 'rt')
    else:
        response = HTTPFound("%s does not have a README file." % test_name)
    return response

@view_config(route_name="stats", renderer="stats.mako",
    permission='view')
def stats(request):
    return {}

@view_config(context=HTTPNotFound, renderer="404.mako")
def not_found(self, request):
    request.response.status = 404
    return {}

@view_config(route_name="old_browser", renderer="old_browser.mako",
    permission='view')
def old_browser(request):
    return {}

# Author: Anthony Rodriguez
# Last Modified: 14 July 2014
def filter_query(request):
    search_params = clean_strings({
                                   'chip_type': request.params.get('chip_type', u''),
                                   'seq_kit_type': request.params.get('seq_kit_type', u'')
                                   })
    
    metrics_query = DBSession.query(MetricsPGM).order_by(MetricsPGM.id.desc())
    
    # BEGIN filter by value
    for column, value in search_params.items():
        if value:
            if column == 'chip_type':
                metrics_query = metrics_query.filter(MetricsPGM.chip_type == value)
            if column == 'seq_kit_type':
                metrics_query = metrics_query.filter(MetricsPGM.seq_kit == value)
    # END filter by value
    
    
    return metrics_query, search_params

# Author: Anthony Rodriguez
# Last Modified: 14 July 2014
@view_config(route_name="analysis", renderer="analysis.mako", permission="view")
def analysis(request):

    pgm_columns = [
                   "ID",
                   "Label",
                   "PGM Temperature",
                   "PGM Pressure",
                   "Chip Temperature",
                   "Chip Noise",
                   "Sequencing Kit",
                   "Chip Type",
                   "ISP Loading",
                   "Signal To Noise Ratio"
                   ]
    
    chip_types = [
                  "314 V1",
                  "314 V2",
                  "316 V1",
                  "316 V2",
                  "318 V1",
                  "318 V2"
                  ]
    
    seq_kit_types = [
                     "PGM Seq 100",
                     "PGM Seq 200",
                     "PGM Seq 200 IC",
                     "PGM Seq 200 v2",
                     "PGM Seq 300",
                     "PGM Seq 400",
                     "PGM Seq Hi-Q TA",
                     ]
    
    metrics_query, search_params = filter_query(request)
    
    # BEGIN Pager
    page = int(request.params.get("page", 1))
    page_url = paginate.PageURL_WebOb(request)
    
    metric_pages = paginate.Page(metrics_query, page, items_per_page=100, url=page_url)
    pages = [metric_pages.first_page]
    left_pagius = 5
    right_pagius = 5
    total = 2 + left_pagius + 1 + right_pagius + 2
    
    if metric_pages.page_count <= total:
        pages = range(1, metric_pages.page_count + 1)
    else:
        if metric_pages.page - left_pagius < 3:
            diff = 3 - (metric_pages.page - left_pagius)
            right_pagius += diff
            left_pagius = max(left_pagius - diff, 0)
        if metric_pages.page + right_pagius > metric_pages.page_count - 2:
            diff = (metric_pages.page + right_pagius + 1) - (metric_pages.page_count - 1)
            left_pagius += diff
            right_pagius = max(right_pagius - diff, 0)
        if metric_pages.page - left_pagius > 3:
            pages.append("..")
        elif metric_pages.page - left_pagius == 3:
            pages.append("2")

        if metric_pages.page > 2:
            pages.extend(range(max(metric_pages.page - left_pagius, 3), metric_pages.page))
        if metric_pages.page >= 2:
            pages.append(metric_pages.page)

        pages.extend(range(metric_pages.page + 1, min(metric_pages.page + right_pagius + 1, metric_pages.page_count)))

        if metric_pages.page + right_pagius < metric_pages.page_count - 2:
            pages.append("..")
        elif metric_pages.page + right_pagius == metric_pages.page_count - 2:
            pages.append(metric_pages.page_count - 1)

        if metric_pages.page < metric_pages.page_count:
            pages.append(metric_pages.page_count)
    # END Pager
    
    return {'metrics': metric_pages, 'pages': pages, 'page_url': page_url, "pgm_columns": pgm_columns, "chip_types": chip_types, "search": search_params,
            'seq_kit_types': seq_kit_types}

# Author: Anthony Rodriguez
# Last Modified: 14 July 2014
@view_config(route_name="analysis_csv", permission="view")
def analysis_csv(request):
    
    pgm_columns = [
                   "ID",
                   "Label",
                   "PGM Temperature",
                   "PGM Pressure",
                   "Chip Temperature",
                   "Chip Noise",
                   "Sequencing Kit",
                   "Chip Type",
                   "ISP Loading",
                   "Signal To Noise Ratio"
                   ]
    
    metrics_query, search_params = filter_query(request)
    
    return Response(make_csv(metrics_query, pgm_columns), content_type="text/csv", content_disposition="attachment; filename=analysis.csv")
