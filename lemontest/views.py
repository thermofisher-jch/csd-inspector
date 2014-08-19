import logging
import transaction
import re
import unicodedata
import mimetypes
import os
import shutil
import os.path
import json
import collections
from operator import itemgetter
from datetime import datetime

from lemontest.models import MetricsPGM
from lemontest.models import MetricsProton
from lemontest.models import Saved_Filters_PGM
from lemontest.models import Saved_Filters_Proton
from lemontest.models import FileProgress

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
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.exceptions import NotFound

from pyramid.response import FileResponse

from sqlalchemy.orm import subqueryload, joinedload
from webhelpers import paginate
import upload
import helpers
from sqlalchemy.sql.expression import column
from collections import OrderedDict
from sqlalchemy.orm.interfaces import collections
import lemontest

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

# validate filter parameters
def validate_filter_params(request, params_only=False):
    numeric_filter_re = re.compile('metric_type_filter\d+')
    numeric_filter_re2 = re.compile('.*_number\d+')
    sorting_filter_re = re.compile('.*_sort')

    extra_params = {}
    search_params = {}
    numeric_filters = {}
    categorical_filters = {}

    for key in request.keys():
        if request[key].strip():
            search_params[key] = request[key].strip()

    for key, value in search_params.items():
        if numeric_filter_re.match(key):
            category = numeric_filter_re.match(key).group()
            category_number = re.findall('\d+', category)
            min_number = 'min_number' + category_number[0]
            max_number = 'max_number' + category_number[0]

            if min_number in search_params and max_number in search_params:
                numeric_filters[key] = {'type': value, 'min': search_params[min_number], 'max': search_params[max_number]}
                search_params[min_number] = ''
                search_params[max_number] = ''
            elif min_number in search_params and max_number not in search_params:
                numeric_filters[key] = {'type': value, 'min': search_params[min_number], 'max': ''}
                search_params[min_number] = ''
            elif min_number not in search_params and max_number in search_params:
                numeric_filters[key] = {'type': value, 'min': '', 'max': search_params[max_number]}
                search_params[max_number] = ''
            search_params[key] = ''

    if 'extra_filter_number' not in search_params:
        numeric_filters['extra_filters'] = u'0'
        extra_params['extra_filters_template'] = u'0'
    else:
        numeric_filters['extra_filters'] = search_params['extra_filter_number']
        extra_params['extra_filters_template'] = search_params['extra_filter_number']
        search_params['extra_filter_number'] = ''

    if 'filterid' not in search_params:
        extra_params['filterid'] = ''
    else:
        extra_params['filterid'] = search_params['filterid']
        search_params['filterid'] = ''

    if 'show_hide' in search_params:
        extra_params['show_hide'] = search_params['show_hide']
        search_params['show_hide'] = ''
    if 'csrf_token' in search_params:
        extra_params['csrf_token'] = search_params['csrf_token']
        search_params['csrf_token'] = ''
    if 'metric_type' in search_params:
        extra_params['metric_type'] = search_params['metric_type']
        search_params['metric_type'] = ''
    if 'page' in search_params:
        extra_params['page'] = search_params['page']
        search_params['page'] = ''
    if 'current_selected_filter' in search_params:
        extra_params['current_selected_filter'] = search_params['current_selected_filter']
        search_params['current_selected_filter'] = ''
    if 'saved_filter_name' in search_params:
        extra_params['saved_filter_name'] = search_params['saved_filter_name']
        search_params['saved_filter_name'] = ''
    if 'saved_filters' in search_params:
        extra_params['saved_filters'] = search_params['saved_filters']
        search_params['saved_filters'] = ''
    if 'taskid' in search_params:
        extra_params['taskid'] = search_params['taskid']
        search_params['taskid'] = ''

    temp = {}
    for key in search_params.keys():
        if search_params[key]:
            temp[key] = search_params[key]
    search_params = temp

    # separate categorical parameters
    # except the ones needed for csrf verification and csv support
    for key, value in search_params.items():
        if not sorting_filter_re.match(key):
            categorical_filters[key] = value

    if params_only:
        return extra_params
    else:
        return categorical_filters, numeric_filters, extra_params

# create filter object
def get_db_queries(request, metric_object_type=None):

    categorical_filters, numeric_filters, extra_params = validate_filter_params(request)

    if not metric_object_type:
        if 'metric_type' not in extra_params or not extra_params['metric_type']:
            return HTTPInternalServerError()
        else:
            metric_type = extra_params['metric_type']

        if metric_type == '/trace/pgm':
            metric_object_type = MetricsPGM
        elif metric_type == '/trace/proton':
            metric_object_type = MetricsProton

    if metric_object_type == MetricsPGM:
        if 'filterid' in extra_params and extra_params['filterid'] and extra_params['filterid'] != 'blank':
            filter_obj = DBSession.query(Saved_Filters_PGM).filter(Saved_Filters_PGM.id == int(extra_params['filterid'])).first()
            extra_params['current_selected_filter'] = filter_obj.name
        else:
            filter_obj = Saved_Filters_PGM('temp', json.dumps(numeric_filters), json.dumps(categorical_filters))
            extra_params['current_selected_filter'] = 'None'
        if not filter_obj:
            filter_obj = Saved_Filters_PGM('not_found', json.dumps(numeric_filters), json.dumps(categorical_filters))
            extra_params['current_selected_filter'] = 'None'

        saved_filters = DBSession.query(Saved_Filters_PGM).order_by(Saved_Filters_PGM.id.desc())
    elif metric_object_type == MetricsProton:
        if 'filterid' in extra_params and extra_params['filterid'] and extra_params['filterid'] != 'blank':
            filter_obj = DBSession.query(Saved_Filters_Proton).filter(Saved_Filters_Proton.id == int(extra_params['filterid'])).first()
            extra_params['current_selected_filter'] = filter_obj.name
        else:
            filter_obj = Saved_Filters_Proton('temp', json.dumps(numeric_filters), json.dumps(categorical_filters))
            extra_params['current_selected_filter'] = 'None'
        if not filter_obj:
            filter_obj = Saved_Filters_Proton('not_found', json.dumps(numeric_filters), json.dumps(categorical_filters))
            extra_params['current_selected_filter'] = 'None'

        saved_filters = DBSession.query(Saved_Filters_Proton).order_by(Saved_Filters_Proton.id.desc())

    return filter_obj, saved_filters, extra_params

# Author: Anthony Rodriguez
def get_filterable_categories_pgm():
    chip_types = []
    seq_kits = []
    run_types = []
    reference_libs = []
    sw_versions = []
    tss_versions = []
    hw_versions = []
    barcode_sets = []

    metrics_query = DBSession.query(MetricsPGM)

    # Distinct Chip Types in database
    chip_types = metrics_query.distinct().order_by(MetricsPGM.chip_type).values(MetricsPGM.chip_type)
    chip_types = [x[0] for x in chip_types]

    # Distinct Seq Kits in database
    seq_kits = metrics_query.distinct().order_by(MetricsPGM.seq_kit).values(MetricsPGM.seq_kit)
    seq_kits = [x[0] for x in seq_kits]

    # Distinct Run Types in database
    run_types = metrics_query.distinct().order_by(MetricsPGM.run_type).values(MetricsPGM.run_type)
    run_types = [x[0] for x in run_types]

    # Distinct Reference Libraries in database
    reference_libs = metrics_query.distinct().order_by(MetricsPGM.reference).values(MetricsPGM.reference)
    reference_libs = [x[0] for x in reference_libs]

    # Distinct SW Versions in database
    sw_versions = metrics_query.distinct().order_by(MetricsPGM.sw_version).values(MetricsPGM.sw_version)
    sw_versions = [x[0] for x in sw_versions]

    # Distinct TSS Versions in database
    tss_versions = metrics_query.distinct().order_by(MetricsPGM.tss_version).values(MetricsPGM.tss_version)
    tss_versions = [x[0] for x in tss_versions]

    # Distinct HW Versions in database
    hw_versions = metrics_query.distinct().order_by(MetricsPGM.hw_version).values(MetricsPGM.hw_version)
    hw_versions = [x[0] for x in hw_versions]

    # Distinct Barcode Sets in database
    barcode_sets = metrics_query.distinct().order_by(MetricsPGM.barcode_set).values(MetricsPGM.barcode_set)
    barcode_sets = [x[0] for x in barcode_sets]

    return chip_types, seq_kits, run_types, reference_libs, sw_versions, tss_versions, hw_versions, barcode_sets

# Author: Anthony Rodriguez
def get_filterable_categories_proton():
    chip_types = []
    seq_kits = []
    run_types = []
    reference_libs = []
    sw_versions = []
    tss_versions = []
    barcode_sets = []

    metrics_query = DBSession.query(MetricsProton)

    # Distinct Chip Types in database
    chip_types = metrics_query.distinct().order_by(MetricsProton.chip_type).values(MetricsProton.chip_type)
    chip_types = [x[0] for x in chip_types]

    # Distinct Seq Kits in database
    seq_kits = metrics_query.distinct().order_by(MetricsProton.seq_kit).values(MetricsProton.seq_kit)
    seq_kits = [x[0] for x in seq_kits]

    # Distinct Run Types in database
    run_types = metrics_query.distinct().order_by(MetricsProton.run_type).values(MetricsProton.run_type)
    run_types = [x[0] for x in run_types]

    # Distinct Reference Libraries in database
    reference_libs = metrics_query.distinct().order_by(MetricsProton.reference).values(MetricsProton.reference)
    reference_libs = [x[0] for x in reference_libs]

    # Distinct SW Versions in database
    sw_versions = metrics_query.distinct().order_by(MetricsProton.sw_version).values(MetricsProton.sw_version)
    sw_versions = [x[0] for x in sw_versions]

    # Distinct TSS Versions in database
    tss_versions = metrics_query.distinct().order_by(MetricsProton.tss_version).values(MetricsProton.tss_version)
    tss_versions = [x[0] for x in tss_versions]

    # Distinct Barcode Sets in database
    barcode_sets = metrics_query.distinct().order_by(MetricsProton.barcode_set).values(MetricsProton.barcode_set)
    barcode_sets = [x[0] for x in barcode_sets]

    return chip_types, seq_kits, run_types, reference_libs, sw_versions, tss_versions, barcode_sets

# Author: Anthony Rodriguez
@view_config(route_name='analysis_proton', renderer='analysis.mako', permission='view')
def analysis_proton(request):
    filter_obj, saved_filters, extra_params = get_db_queries(request.params, MetricsProton)

    metrics_query = filter_obj.get_query()

    chip_types, seq_kits, run_types, reference_libs, sw_versions, tss_versions, hw_versions, barcode_sets = get_filterable_categories_pgm()

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

    return {'metrics': metric_pages, 'pages': pages, 'page_url': page_url, "search": extra_params, "metric_object_type": MetricsProton,
            "show_hide_defaults": json.dumps(MetricsProton.show_hide_defaults), "show_hide_false": json.dumps(MetricsProton.show_hide_false),
            "metric_columns": json.dumps(MetricsProton.numeric_columns), "filter_name": filter_obj.name, "numeric_filters_json": filter_obj.numeric_filters,
            'categorical_filters_json': filter_obj.categorical_filters, 'chip_types': chip_types, 'seq_kits': seq_kits,
            "run_types": run_types, "reference_libs": reference_libs, "sw_versions": sw_versions, "tss_versions": tss_versions,
            "hw_versions": hw_versions, "barcode_sets": barcode_sets, "saved_filters": saved_filters}

# Author: Anthony Rodriguez
@view_config(route_name='analysis_pgm', renderer="analysis.mako", permission="view")
def analysis_pgm(request):
    filter_obj, saved_filters, extra_params = get_db_queries(request.params, MetricsPGM)

    metrics_query = filter_obj.get_query()

    chip_types, seq_kits, run_types, reference_libs, sw_versions, tss_versions, hw_versions, barcode_sets = get_filterable_categories_pgm()

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

    return {'metrics': metric_pages, 'pages': pages, 'page_url': page_url, "search": extra_params, "metric_object_type": MetricsPGM,
            "show_hide_defaults": json.dumps(MetricsPGM.show_hide_defaults), "show_hide_false": json.dumps(MetricsPGM.show_hide_false),
            "metric_columns": json.dumps(MetricsPGM.numeric_columns), "filter_name": filter_obj.name, "numeric_filters_json": filter_obj.numeric_filters,
            'categorical_filters_json': filter_obj.categorical_filters, 'chip_types': chip_types, 'seq_kits': seq_kits,
            "run_types": run_types, "reference_libs": reference_libs, "sw_versions": sw_versions, "tss_versions": tss_versions,
            "hw_versions": hw_versions, "barcode_sets": barcode_sets, "saved_filters": saved_filters}

#Author: Anthony Rodriguez
@view_config(route_name="analysis_show_hide", renderer="json", permission="view", xhr=True)
def show_hide_columns(request):

    show_hide_columns = {}

    request_path = request.params.get("metric_type")

    if request_path == '/trace/pgm':
        if "show_hide_columns/trace/pgm" in request.POST and request.POST['show_hide_columns/trace/pgm']:
            show_hide_columns = request.params.get("show_hide_columns/trace/pgm")
    elif request_path == '/trace/proton':
        if "show_hide_columns/trace/proton" in request.POST and request.POST['show_hide_columns/trace/proton']:
            show_hide_columns = request.params.get("show_hide_columns/trace/proton")

    if request_path == '/trace/pgm':
        request.session["show_hide_session/trace/pgm"]= show_hide_columns
    elif request_path == '/trace/proton':
        request.session["show_hide_session/trace/proton"]= show_hide_columns

    return {"status": 200}

def does_filter_exist(filter_object):
    '''
    check hash of filter_object to see if it already exists in the db
    if it does exist return true and the id, else false and empty string
    '''
    return False, ''

@view_config(context=HTTPInternalServerError, renderer='404.mako')
def server_error(self, request):
    request.response.status = 500
    return {}

# Author: Anthony Rodriguez
@view_config(route_name="analysis_csv", permission="view")
def analysis_csv(request):
    filter_obj, saved_filters, extra_params = get_db_queries(request.params)

    if 'metric_type' not in extra_params or not extra_params['metric_type']:
        return HTTPInternalServerError()
    else:
        metric_type = extra_params['metric_type']

    if metric_type == '/trace/pgm':
        metric_object_type = MetricsPGM
        filter_object_type = Saved_Filters_PGM
    elif metric_type == '/trace/proton':
        metric_object_type = MetricsProton
        filter_object_type = Saved_Filters_Proton

    file_progress = FileProgress('csv')
    DBSession.add(file_progress)
    transaction.commit()

    '''
    if the filter_object hash already exists, query db and pass id to celery task
    else pass entire request to celery task so that the task can create the filter object
    '''
    filter_exists, filter_id = does_filter_exist(filter_obj)

    if not filter_exists:
        filter_id = extra_params['filterid']

    if filter_exists or filter_id:
        filter_obj = DBSession.query(filter_object_type).filter(filter_object_type.id == filter_id).first()
        celery_task = lemontest.csv_support.make_csv.delay(metric_object_type, filter_object_type, file_progress.id, extra_params['show_hide'], filter_id=filter_obj.id)
    else:
        celery_task = lemontest.csv_support.make_csv.delay(metric_object_type, filter_object_type, file_progress.id, extra_params['show_hide'], request=request.params)

    url = request.route_url('analysis_csv_update')
    url += '?taskid=' + str(celery_task.id)
    url += '&metric_type=' + metric_type
    return HTTPFound(location=url)

@view_config(route_name='analysis_csv_update', renderer='json', permission='view')
def check_csv_file(request):

    extra_params = validate_filter_params(request.params, params_only=True)

    task_id = extra_params.get('taskid', '')
    metric_type = extra_params.get('metric_type', '')
    if not task_id:
        task_id = request.session['file_pending' + metric_type]
    else:
        request.session['file_pending' + metric_type] = task_id

    file_progress = DBSession.query(FileProgress).filter(FileProgress.celery_id == unicode(task_id)).first()

    if file_progress:
        if file_progress.status != "Done":
            return {'status': 'pending', 'task_id': task_id}
        else:
            return {'status': 'done', 'id': file_progress.id}
    else:
        return {'status': 'pending', 'task_id': task_id}

@view_config(route_name='analysis_serve_csv', renderer='json', permission='view')
def serve_csv_file(request):
    metric_type = request.params.get('metric_type', '')

    request.session['file_pending' + metric_type] = ''

    file = DBSession.query(FileProgress).filter(FileProgress.id == request.params['file_id']).first()
    response = FileResponse(file.path, request=request, content_type='text/csv')
    response.headers['Content-Disposition'] = "attachment; filename=analysis.csv"
    return response

@view_config(route_name='analysis_apply_filter', renderer="json", permission='view')
def apply_filter(request):
    if 'metric_type' in request.params and request.params['metric_type'].strip() == '/trace/pgm':
        url = request.route_url('analysis_pgm')
        url += '?filterid=' + request.params['filterid']
    elif 'metric_type' in request.params and request.params['metric_type'].strip() == '/trace/proton':
        url = request.route_url('analysis_proton')
        url += '?filterid=' + request.params['filterid']

    return HTTPFound(location=url)

@view_config(route_name="analysis_save_filter", renderer="json", permission="view")
def save_filter(request):
    if 'metric_type' in request.params and request.params['metric_type'].strip() == '/trace/pgm':
        filter_obj, saved_filters, extra_params = get_db_queries(request.params, MetricsPGM)
        filter_obj.name = extra_params['saved_filter_name']
        if (len(filter_obj.numeric_filters_json) > 1) or filter_obj.categorical_filters_json:
            DBSession.add(filter_obj)
            DBSession.flush()
            url = request.route_url('analysis_pgm')
            url += '?filterid=' + str(filter_obj.id)
            transaction.commit()
        else:
            url = request.route_url('analysis_pgm')
            url += '?filterid=blank'
    elif 'metric_type' in request.params and request.params['metric_type'].strip() == '/trace/proton':
        filter_obj, saved_filters, extra_params = get_db_queries(request.params, MetricsProton)
        filter_obj.name = extra_params['saved_filter_name']
        if (len(filter_obj.numeric_filters_json) > 1) or filter_obj.categorical_filters_json:
            DBSession.add(filter_obj)
            DBSession.flush()
            url = request.route_url('analysis_proton')
            url += '?filterid=' + str(filter_obj.id)
            transaction.commit()
        else:
            url = request.route_url('analysis_proton')
            url += '?filterid=blank'

    return HTTPFound(location=url)

@view_config(route_name='analysis_delete_saved_filter', renderer='json', permission='view')
def delete_saved_filter(request):
    filter_id = request.params.get('filter_to_delete', '')
    filter_type = request.params.get('metric_type', '')

    if filter_id:
        if filter_type == '/trace/pgm':
            url = request.route_url('analysis_pgm')
            filter = DBSession.query(Saved_Filters_PGM).filter(Saved_Filters_PGM.id == filter_id).first()
            DBSession.delete(filter)
            transaction.commit()
        elif filter_type == '/trace/proton':
            url = request.route_url('analysis_proton')
            filter = DBSession.query(Saved_Filters_Proton).filter(Saved_Filters_Proton.id == filter_id).first()
            DBSession.delete(filter)
            transaction.commit()

    return HTTPFound(location=url)