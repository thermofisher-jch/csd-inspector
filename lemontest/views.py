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
from datetime import datetime

from lemontest.models import MetricsPGM
from lemontest.models import MetricsProton
from lemontest.models import MetricsOTLog

from lemontest.models import SavedFilters

from lemontest.models import FileProgress

from lemontest.models import Graph
from lemontest.models import MetricReport

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

trace_graph_types = [
                     'boxplot',
                     'histogram',
                     ]

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

'''BEGIN METRIC PAGE VIEWS'''
# Author: Anthony Rodriguez
@view_config(route_name='trace_pgm', renderer="trace.pgm.mako", permission="view")
def trace_pgm(request):
    '''create filter object, get saved filters in db, and all extra parameters that were not used'''
    filter_obj, saved_filters, extra_params, sort_by_column = get_db_queries(request.params, 'pgm')

    '''get query set that corresponds with filter object'''
    metrics_query = filter_obj.get_query()

    temp = []
    if sort_by_column:
        column, order = sort_by_column.items()[0]
        if order == 'sorting_asc':
            if column == 'ID':
                metrics_query = metrics_query.order_by(Archive.id.asc())
                temp.append("id")
            elif column == 'Label':
                metrics_query = metrics_query.order_by(Archive.label.asc())
                temp.append("label")
            elif column == 'Upload Time':
                metrics_query = metrics_query.order_by(Archive.time.asc())
                temp.append("upload_time")
            elif column in MetricsPGM.columns:
                metrics_query = metrics_query.order_by(MetricsPGM.get_column(column).asc())
                temp.append(str(MetricsPGM.get_column(column)).split('.')[1])
        elif order == 'sorting_desc':
            if column == 'ID':
                metrics_query = metrics_query.order_by(Archive.id.desc())
                temp.append("id")
            elif column == 'Label':
                metrics_query = metrics_query.order_by(Archive.label.desc())
                temp.append("label")
            elif column == 'Upload Time':
                metrics_query = metrics_query.order_by(Archive.time.desc())
                temp.append("upload_time")
            elif column in MetricsPGM.columns:
                metrics_query = metrics_query.order_by(MetricsPGM.get_column(column).desc())
                temp.append(str(MetricsPGM.get_column(column)).split('.')[1])
        else:
            metrics_query = metrics_query.order_by(Archive.id.desc())
        temp.append(order)
        sort_by_column = temp
    else:
        metrics_query = metrics_query.order_by(Archive.id.desc())
        temp.append("id")
        temp.append("sorting_desc")
        sort_by_column = temp

    '''get categorical values from the database'''
    chip_types, seq_kits, run_types, reference_libs, sw_versions, tss_versions, hw_versions, barcode_sets = get_filterable_categories_pgm()

    '''BEGIN PAGINATE QUERY RESULTS'''
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
    '''END PAGINATE QUERY RESULTS'''

    return {'metrics': metric_pages, 'pages': pages, 'page_url': page_url, "search": extra_params, "sort_by_column": json.dumps(sort_by_column), "metric_object_type": MetricsPGM,
            "show_hide_defaults": json.dumps(MetricsPGM.show_hide_defaults), "show_hide_false": json.dumps(MetricsPGM.show_hide_false),
            "metric_columns": json.dumps(MetricsPGM.numeric_columns), "filter_name": filter_obj.name, "filter_id": filter_obj.id, "numeric_filters_json": filter_obj.numeric_filters,
            'categorical_filters_json': filter_obj.categorical_filters, 'chip_types': chip_types, 'seq_kits': seq_kits,
            "run_types": run_types, "reference_libs": reference_libs, "sw_versions": sw_versions, "tss_versions": tss_versions,
            "hw_versions": hw_versions, "barcode_sets": barcode_sets, "saved_filters": saved_filters}

# Author: Anthony Rodriguez
@view_config(route_name='trace_proton', renderer='trace.proton.mako', permission='view')
def trace_proton(request):
    '''create filter object, get saved filters in db, and all extra parameters that were not used'''
    filter_obj, saved_filters, extra_params, sort_by_column = get_db_queries(request.params, 'proton')

    '''get query set that corresponds with filter object'''
    metrics_query = filter_obj.get_query()

    '''get categorical values from the database'''
    chip_types, seq_kits, run_types, reference_libs, sw_versions, tss_versions, hw_versions, barcode_sets = get_filterable_categories_proton()

    '''BEGIN PAGINATE QUERY RESULTS'''
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
    '''END PAGINATE QUERY RESULTS'''

    return {'metrics': metric_pages, 'pages': pages, 'page_url': page_url, "search": extra_params, "metric_object_type": MetricsProton,
            "show_hide_defaults": json.dumps(MetricsProton.show_hide_defaults), "show_hide_false": json.dumps(MetricsProton.show_hide_false),
            "metric_columns": json.dumps(MetricsProton.numeric_columns), "filter_name": filter_obj.name, "numeric_filters_json": filter_obj.numeric_filters,
            'categorical_filters_json': filter_obj.categorical_filters, 'chip_types': chip_types, 'seq_kits': seq_kits,
            "run_types": run_types, "reference_libs": reference_libs, "sw_versions": sw_versions, "tss_versions": tss_versions,
            "hw_versions": hw_versions, "barcode_sets": barcode_sets, "saved_filters": saved_filters}

# Author: Anthony Rodriguez
@view_config(route_name='trace_otlog', renderer='trace.otlog.mako', permission='view')
def trace_otlog(request):
    '''create filter object, get saved filters in db, and all extra parameters that were not used'''
    filter_obj, saved_filters, extra_params, sort_by_column = get_db_queries(request.params, 'otlog')

    '''get query set that corresponds with filter object'''
    metrics_query = filter_obj.get_query()

    '''get categorical values from the database'''
    ot_version, sample_inject_abort, oil_pump_status, sample_pump_status = get_filterable_categories_otlog()

    '''BEGIN PAGINATE QUERY RESULTS'''
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
    '''END PAGINATE QUERY RESULTS'''

    return {'metrics': metric_pages, 'pages': pages, 'page_url': page_url, "search": extra_params, "metric_object_type": MetricsOTLog,
            "show_hide_defaults": json.dumps(MetricsOTLog.show_hide_defaults), "show_hide_false": json.dumps(MetricsOTLog.show_hide_false),
            "metric_columns": json.dumps(MetricsOTLog.numeric_columns), "filter_name": filter_obj.name, "numeric_filters_json": filter_obj.numeric_filters,
            'categorical_filters_json': filter_obj.categorical_filters, 'ot_version': ot_version, 'sample_inject_abort': sample_inject_abort,
            'oil_pump_status': oil_pump_status, 'sample_pump_status': sample_pump_status, "saved_filters": saved_filters}

'''END METRIC PAGE VIEWS'''

#Author: Anthony Rodriguez
# create filter object
def get_db_queries(request, metric_type=None):
    '''validate request parameters'''
    categorical_filters, numeric_filters, sort_by_column, extra_params = validate_filter_params(request)

    '''make sure we have metric_type'''
    if not metric_type:
        if 'metric_type' not in extra_params or not extra_params['metric_type']:
            return HTTPInternalServerError()
        else:
            metric_type = extra_params['metric_type']

    '''if request is for an existing saved filter, query db and return that filter
    filterid could be set to blank if user tries to save an empty filterset'''
    if 'filterid' in extra_params and extra_params['filterid'] and extra_params['filterid'] != 'blank':
        filter_obj = DBSession.query(SavedFilters).filter(SavedFilters.id == int(extra_params['filterid'])).first()

        if filter_obj:
            extra_params['current_selected_filter'] = filter_obj.name
        else:
            filter_obj = SavedFilters('not_found', metric_type, json.dumps(numeric_filters), json.dumps(categorical_filters))
            extra_params['current_selected_filter'] = 'None'
    else:
        filter_obj = SavedFilters('None', metric_type, json.dumps(numeric_filters), json.dumps(categorical_filters))
        filter_obj.type = 'temp'
        extra_params['current_selected_filter'] = 'None'

    '''gets all saved filters from bd'''
    saved_filters = DBSession.query(SavedFilters).filter(SavedFilters.metric_type == metric_type).filter(SavedFilters.type != "temp").order_by(SavedFilters.id.desc())

    return filter_obj, saved_filters, extra_params, sort_by_column

#Author: Anthony Rodriguez
# validate parameters
def validate_filter_params(request, params_only=False):
    '''parameters that the template is expecting will always be there and default values if not found'''
    required_params = {
                       "extra_filters_template": u'0',
                       "filterid": '',
                       }

    '''parameters that are used throughout the app'''
    used_params = [
                   'show_hide',
                   'csrf_token',
                   'metric_type',
                   'page',
                   'current_selected_filter',
                   'saved_filter_name',
                   'saved_filters',
                   'fileprogress_id',
                   'report_id',
                   'graph_column_name',
                   'graph_type',
                   'report',
                   ]

    '''regular expression to find numeric filter parameters'''
    numeric_filter_re = re.compile('metric_type_filter\d+')
    numeric_filter_re2 = re.compile('.*_number\d+')
    sorting_filter_re = re.compile('.*_sort')

    '''regular expressions to find report customization'''
    report_custom_re = re.compile('boxplot_.*')
    report_custom_re2 = re.compile('histogram_.*')

    extra_params = {}
    search_params = {}
    numeric_filters = {}
    categorical_filters = {}
    sort_by_column = {}

    '''grab only non-empty parameters'''
    for key in request.keys():
        if request[key].strip():
            search_params[key] = request[key].strip()

    '''find all parameters for numeric filters
    remove them from search_params after use'''
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
        elif report_custom_re.match(key) or report_custom_re2.match(key):
            extra_params[key] = value
            search_params[key] = ''

    '''find and remove all numeric filter stragglers
    that result from incomplete numeric filter forms'''
    for key in search_params.keys():
        if numeric_filter_re2.match(key):
            search_params[key] = ''

    '''look for all required params and set to default value if not found'''
    for param, default_value in required_params.items():
        if param not in search_params:
            extra_params[param] = default_value
        else:
            extra_params[param] = search_params[param]
            search_params[param] = ''

    '''needed param for numeric filters'''
    numeric_filters['extra_filters'] = extra_params['extra_filters_template']

    '''separate all non filter params out'''
    for param in used_params:
        if param in search_params:
            extra_params[param] = search_params[param]
            search_params[param] = ''

    # keep all non empty params
    '''at this point it will be all categorical parameters and column sorting'''
    temp = {}
    for key in search_params.keys():
        if search_params[key]:
            temp[key] = search_params[key]
    search_params = temp

    '''separate categorical parameters'''
    for key, value in search_params.items():
        if not sorting_filter_re.match(key):
            categorical_filters[key] = value
        else:
            sort_by_column[key.split('_sort')[0]] = value

    '''if params_only flag is set, returns only extra_params'''
    if params_only:
        return extra_params
    else:
        return categorical_filters, numeric_filters, sort_by_column, extra_params

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

    '''Distinct Chip Types in database'''
    chip_types = metrics_query.distinct().order_by(MetricsPGM.chip_type).values(MetricsPGM.chip_type)
    chip_types = [x[0] for x in chip_types]

    '''Distinct Seq Kits in database'''
    seq_kits = metrics_query.distinct().order_by(MetricsPGM.seq_kit).values(MetricsPGM.seq_kit)
    seq_kits = [x[0] for x in seq_kits]

    '''Distinct Run Types in database'''
    run_types = metrics_query.distinct().order_by(MetricsPGM.run_type).values(MetricsPGM.run_type)
    run_types = [x[0] for x in run_types]

    '''Distinct Reference Libraries in database'''
    reference_libs = metrics_query.distinct().order_by(MetricsPGM.reference).values(MetricsPGM.reference)
    reference_libs = [x[0] for x in reference_libs]

    '''Distinct SW Versions in database'''
    sw_versions = metrics_query.distinct().order_by(MetricsPGM.sw_version).values(MetricsPGM.sw_version)
    sw_versions = [x[0] for x in sw_versions]

    '''Distinct TSS Versions in database'''
    tss_versions = metrics_query.distinct().order_by(MetricsPGM.tss_version).values(MetricsPGM.tss_version)
    tss_versions = [x[0] for x in tss_versions]

    '''Distinct HW Versions in database'''
    hw_versions = metrics_query.distinct().order_by(MetricsPGM.hw_version).values(MetricsPGM.hw_version)
    hw_versions = [x[0] for x in hw_versions]

    '''Distinct Barcode Sets in database'''
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
    hw_versions = []
    barcode_sets = []

    metrics_query = DBSession.query(MetricsProton)

    '''Distinct Chip Types in database'''
    chip_types = metrics_query.distinct().order_by(MetricsProton.chip_type).values(MetricsProton.chip_type)
    chip_types = [x[0] for x in chip_types]

    '''Distinct Seq Kits in database'''
    seq_kits = metrics_query.distinct().order_by(MetricsProton.seq_kit).values(MetricsProton.seq_kit)
    seq_kits = [x[0] for x in seq_kits]

    '''Distinct Run Types in database'''
    run_types = metrics_query.distinct().order_by(MetricsProton.run_type).values(MetricsProton.run_type)
    run_types = [x[0] for x in run_types]

    '''Distinct Reference Libraries in database'''
    reference_libs = metrics_query.distinct().order_by(MetricsProton.reference).values(MetricsProton.reference)
    reference_libs = [x[0] for x in reference_libs]

    '''Distinct SW Versions in database'''
    sw_versions = metrics_query.distinct().order_by(MetricsProton.sw_version).values(MetricsProton.sw_version)
    sw_versions = [x[0] for x in sw_versions]

    '''Distinct TSS Versions in database'''
    tss_versions = metrics_query.distinct().order_by(MetricsProton.tss_version).values(MetricsProton.tss_version)
    tss_versions = [x[0] for x in tss_versions]

    '''Distinct Barcode Sets in database'''
    barcode_sets = metrics_query.distinct().order_by(MetricsProton.barcode_set).values(MetricsProton.barcode_set)
    barcode_sets = [x[0] for x in barcode_sets]

    return chip_types, seq_kits, run_types, reference_libs, sw_versions, tss_versions, hw_versions, barcode_sets

# Author: Anthony Rodriguez
def get_filterable_categories_otlog():
    ot_version = []
    sample_inject_abort = []
    oil_pump_status = []
    sample_pump_status = []

    metrics_query = DBSession.query(MetricsOTLog)

    '''Distinct OT Versions in database'''
    ot_version = metrics_query.distinct().order_by(MetricsOTLog.ot_version).values(MetricsOTLog.ot_version)
    ot_version = [x[0] for x in ot_version]

    '''Distinct Sample Inject Abort in  database'''
    sample_inject_abort = metrics_query.distinct().order_by(MetricsOTLog.sample_inject_abort).values(MetricsOTLog.sample_inject_abort)
    sample_inject_abort = [x[0] for x in sample_inject_abort]

    '''Distinct OT Versions in database'''
    oil_pump_status = metrics_query.distinct().order_by(MetricsOTLog.oil_pump_status).values(MetricsOTLog.oil_pump_status)
    oil_pump_status = [x[0] for x in oil_pump_status]

    '''Distinct OT Versions in database'''
    sample_pump_status = metrics_query.distinct().order_by(MetricsOTLog.sample_pump_status).values(MetricsOTLog.sample_pump_status)
    sample_pump_status = [x[0] for x in sample_pump_status]

    return ot_version, sample_inject_abort, oil_pump_status, sample_pump_status

'''BEGIN CSV SUPPORT'''
# Author: Anthony Rodriguez
@view_config(route_name="trace_request_csv", renderer='json', permission="view")
def request_csv(request):
    '''create filter object, get saved filters in db, and all extra parameters that were not used'''
    filter_obj, saved_filters, extra_params, sort_by_column = get_db_queries(request.params)

    if 'metric_type' not in extra_params or not extra_params['metric_type']:
        return {'status': 'error', 'message': 'metric type not in data'}
    else:
        metric_type = extra_params['metric_type']

    '''create file_progress object to track file progress'''
    file_progress = FileProgress('csv')
    DBSession.add(file_progress)
    DBSession.flush()
    file_progress_id = file_progress.id
    transaction.commit()

    '''if the file is a temporary file we want to add it to the DB here
    so that we can pass the id to celery tasks'''
    if filter_obj.type == 'temp':
        DBSession.add(filter_obj)

    '''sets relational ids on filter object for future use'''
    filter_obj.progress_id = file_progress_id
    DBSession.flush()
    filter_object_id = filter_obj.id
    transaction.commit()

    '''calls celery task'''
    celery_task = lemontest.csv_support.make_csv.delay(metric_type, file_progress_id, filter_object_id, extra_params['show_hide'], sort_by_column)

    '''sets celery task id for file progress object'''
    file_progress = DBSession.query(FileProgress).filter(FileProgress.id == file_progress_id).first()
    file_progress.celery_id = celery_task.id
    transaction.commit()

    '''creates a pending file in session for the user'''
    request.session['file_pending_' + metric_type] = file_progress_id

    return {'status': 'ok', 'fileprogress_id': file_progress_id}

# Author: Anthony Rodriguez
@view_config(route_name='trace_serve_csv', renderer='json', permission='view')
def serve_csv(request):
    metric_type = request.params.get('metric_type', '')

    request.session['file_pending_' + metric_type] = ''

    file = DBSession.query(FileProgress).filter(FileProgress.id == request.params['file_id']).first()
    response = FileResponse(file.path, request=request, content_type='text/csv')
    response.headers['Content-Disposition'] = "attachment; filename=trace.csv"
    return response
'''END CSV SUPPORT'''

'''BEGIN PLOT SUPPORT'''
@view_config(route_name='trace_request_report', renderer='json', permission='view')
def request_report(request):
    '''create filter object, get saved filters in db, and all extra parameters that were not used'''
    filter_obj, saved_filters, extra_params, sort_by_column = get_db_queries(request.params)

    if 'metric_type' not in extra_params or not extra_params['metric_type']:
        return {'status': 'error', 'message': 'metric type not in data'}
    else:
        metric_type = extra_params['metric_type']

    if 'graph_column_name' not in extra_params or not extra_params['graph_column_name']:
        return {'status': 'error', 'message': 'no column selected'}
    else:
        metric_column = extra_params['graph_column_name']

    metric_report = MetricReport(metric_type, metric_column)
    DBSession.add(metric_report)
    DBSession.flush()
    metric_report_id = metric_report.id
    transaction.commit()

    '''if the file is a temporary file we want to add it to the DB here
    so that we can pass the id to celery tasks'''
    if filter_obj.type == 'temp':
        DBSession.add(filter_obj)
        DBSession.flush()
        filter_id = filter_obj.id
        transaction.commit()
    else:
        filter_id = filter_obj.id

    metric_report = DBSession.query(MetricReport).filter(MetricReport.id == metric_report_id).first()
    metric_report.filter_id = filter_id
    transaction.commit()

    for graph_type in trace_graph_types:
        '''create file_progress object to track file progress'''
        file_progress = FileProgress('plot')
        DBSession.add(file_progress)
        DBSession.flush()
        file_progress_id = file_progress.id
        transaction.commit()

        filter_obj = DBSession.query(SavedFilters).filter(SavedFilters.id == filter_id).first()
        filter_obj.progress_id = file_progress_id
        transaction.commit()

        graph = Graph(metric_report_id, graph_type, metric_column, file_progress_id)
        DBSession.add(graph)
        transaction.commit()

    celery_task = lemontest.metric_report.make_plots.delay(metric_report_id, filter_id)

    url = request.route_url('trace_show_report')
    url += '?report=' + str(metric_report_id)

    return HTTPFound(location=url)

@view_config(route_name='trace_customize_report', renderer='json', permission='view')
def customize_report(request):
    report_custom_re = re.compile('boxplot_.*')
    report_custom_re2 = re.compile('histogram_.*')

    boxplot_specs = {}
    histogram_specs = {}

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    extra_params = validate_filter_params(request.params, params_only=True)

    for key, value in extra_params.items():
        if report_custom_re.match(key):
            boxplot_specs[key] = value
        elif report_custom_re2.match(key):
            histogram_specs[key] = value

    if "report" not in extra_params or not extra_params['report']:
        return HTTPInternalServerError()
    else:
        report_id = extra_params['report']

    report = DBSession.query(MetricReport).filter(MetricReport.id == report_id).first()

    if not report:
        return {'status': 'not_found', 'url': request.route_path('index')}
    else:
        filter_id = report.filter_id
        metric_type = report.metric_type
        metric_column = report.metric_column

    celery_task = lemontest.metric_report.customize_plots.delay(report_id, filter_id, boxplot_specs, histogram_specs)

    url = request.route_url('trace_show_report')
    url += '?report=' + str(report_id)

    return HTTPFound(location=url)

# Author: Anthony Rodriguez
@view_config(route_name='trace_show_report', renderer='trace.report.mako', permission='view')
def show_report(request):
    numeric_filter_re = re.compile('metric_type_filter\d+')

    if "report" not in request.params or not request.params['report']:
        return HTTPInternalServerError()
    else:
        report_id = request.params['report']

    report = DBSession.query(MetricReport).filter(MetricReport.id == report_id).first()

    if not report:
        return {'status': 'not_found', 'url': request.route_path('index')}

    filter_obj = DBSession.query(SavedFilters).filter(SavedFilters.id == report.filter_id).first()

    filter_params = {}
    for key, value in filter_obj.numeric_filters_json.items():
        if numeric_filter_re.match(key):
            if value['min'] and value['max']:
                filter_params[filter_obj.numeric_filters_json[key]['type']] = str(value['min']) + " - " + str(value['max'])
            elif value['min'] and not value['max']:
                filter_params[filter_obj.numeric_filters_json[key]['type']] = "> " + str(value['min'])
            else:
                filter_params[filter_obj.numeric_filters_json[key]['type']] = "<" + str(value['max'])

    for key, value in filter_obj.categorical_filters_json.items():
        filter_params[key] = value

    return {'status': 'found', 'report': report, 'filter_obj': filter_obj, 'filter_params': filter_params}

# Author: Anthony Rodriguez
@view_config(route_name='trace_check_report_update', renderer='json', permission='view')
def check_report_update(request):
    extra_params = validate_filter_params(request.params, params_only=True)

    if 'report_id' not in extra_params or not extra_params['report_id']:
        return {'status': 'error', 'request': request.params.items()}

    report_id = extra_params['report_id']

    report = DBSession.query(MetricReport).filter(MetricReport.id == report_id).first()

    status = {}

    '''if one exists we check its status, and update UI'''
    if report:
        status['report'] = {'status': report.status, 'statistics': report.get_statistics()}
        for graph in report.graphs:
            current_graph = DBSession.query(Graph).filter(Graph.id == graph.id).first()
            graph_type = str(current_graph.graph_type)
            status[graph_type] = {'status': current_graph.fileprogress.status, 'src': current_graph.fileprogress.path, 'graph_details': graph.get_details()}

        return {'status': 'found', 'data': json.dumps(status)}
    else:
        return {'status': 'not_found', 'report_id': report_id}
'''END PLOT SUPPORT'''

# Author: Anthony Rodriguez
@view_config(route_name='trace_check_file_update', renderer='json', permission='view')
def check_file_update(request):
    file_pending_re = re.compile('file_pending.*')

    extra_params = validate_filter_params(request.params, params_only=True)

    '''if for some reason we loose the progress id, we send back an error and clear user session'''
    if 'fileprogress_id' not in extra_params or not extra_params['fileprogress_id']:
        for key in request.session.keys():
            if file_pending_re.match(key):
                request.session[key] = ''
        return {'status': 'error', 'request': request.params.items()}
    if 'metric_type' not in extra_params or not extra_params['metric_type']:
        for key in request.session.keys():
            if file_pending_re.match(key):
                request.session[key] = ''
        return {'status': 'error', 'request': request.params.items()}

    fileprogress_id = extra_params['fileprogress_id']
    metric_type = extra_params['metric_type']

    '''find file progress object'''
    file_progress_obj = DBSession.query(FileProgress).filter(FileProgress.id == fileprogress_id).first()

    '''if one exists we check its status, and update UI'''
    if file_progress_obj:
        if file_progress_obj.status == "Done":
            return {'status': 'done', 'fileprogress_id': fileprogress_id, 'progress': 1}
        elif file_progress_obj.status == "Error":
            return {'status': 'error', 'message': "File progress ended in an error"}
        else:
            return {'status': 'pending', 'fileprogress_id': fileprogress_id, 'progress': file_progress_obj.progress}
    else:
        return {'status': 'pending', 'fileprogress_id': fileprogress_id, 'progress': 0}

#Author: Anthony Rodriguez
@view_config(route_name="trace_show_hide", renderer="json", permission="view", xhr=True)
def show_hide_columns(request):

    show_hide_columns = {}

    metric_type = request.params.get("metric_type")

    show_hide = "show_hide_columns_" + metric_type

    if show_hide in request.POST and request.POST[show_hide]:
        show_hide_columns = request.params.get(show_hide)

    request.session['show_hide_session_' + metric_type] = show_hide_columns

    return {"status": 200}

#Author: Anthony Rodriguez
@view_config(route_name='trace_apply_filter', renderer="json", permission='view')
def apply_filter(request):
    if 'metric_type' in request.params and request.params['metric_type'].strip() == 'pgm':
        url = request.route_url('trace_pgm')
        url += '?filterid=' + request.params['filterid']
    elif 'metric_type' in request.params and request.params['metric_type'].strip() == 'proton':
        url = request.route_url('trace_proton')
        url += '?filterid=' + request.params['filterid']

    return HTTPFound(location=url)

#Author: Anthony Rodriguez
@view_config(route_name="trace_save_filter", renderer="json", permission="view")
def save_filter(request):

    filter_obj, saved_filters, extra_params, sort_column = get_db_queries(request.params)

    if 'metric_type' not in extra_params or not extra_params['metric_type']:
        return HTTPInternalServerError()
    else:
        metric_type = extra_params['metric_type']

    if metric_type == 'pgm':
        url = request.route_url('trace_pgm')
    elif metric_type == 'proton':
        url = request.route_url('trace_proton')
    elif metric_type == 'otlog':
        url = request.route_url('trace_otlog')

    filter_obj.name = extra_params['saved_filter_name']
    if (len(filter_obj.numeric_filters_json) > 1) or filter_obj.categorical_filters_json:
        filter_obj.type = "saved"
        DBSession.add(filter_obj)
        DBSession.flush()
        url += '?filterid=' + str(filter_obj.id)
        transaction.commit()
    else:
        url += '?filterid=blank'

    return HTTPFound(location=url)

#Author: Anthony Rodriguez
@view_config(route_name='trace_delete_saved_filter', renderer='json', permission='view')
def delete_saved_filter(request):
    filter_id = request.params.get('filter_to_delete', '')
    filter_type = request.params.get('metric_type', '')

    if filter_id:
        filter = DBSession.query(SavedFilters).filter(SavedFilters.id == filter_id).first()
        DBSession.delete(filter)
        transaction.commit()

        if filter_type == 'pgm':
            url = request.route_url('trace_pgm')
        elif filter_type == 'proton':
            url = request.route_url('trace_proton')

    return HTTPFound(location=url)

'''DEBUG'''

#Author: Anthony Rodriguez
# useful when trying to see what is in the DB
@view_config(route_name='db_query', renderer='db_objects.mako', permission='view')
def db_query(request):
    file_progress_query = DBSession.query(FileProgress).all()
    graphs_query = DBSession.query(Graph).all()
    metric_reports_query = DBSession.query(MetricReport).all()

    saved_filters = DBSession.query(SavedFilters).all()

    archive_query = DBSession.query(Archive).all()
    metrics_pgm_query = DBSession.query(MetricsPGM).all()
    metrics_proton_query = DBSession.query(MetricsProton).all()
    metrics_otlog_query = DBSession.query(MetricsOTLog).all()

    db_entities = {
                   'file_progress_query': file_progress_query,
                   'graphs_query': graphs_query,
                   'metric_reports_query': metric_reports_query,
                   'saved_filters': saved_filters,
                   'archive_query': archive_query,
                   'metrics_pgm_query': metrics_pgm_query,
                   'metrics_proton_query': metrics_proton_query,
                   'metrics_otlog_query': metrics_otlog_query
                   }

    #commented out but used to reset user session
    #request.session.invalidate()

    return {'db_entities': db_entities}