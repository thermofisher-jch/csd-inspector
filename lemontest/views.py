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
from lemontest.csv_support import make_csv

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
from sqlalchemy.sql.expression import column
from collections import OrderedDict
from sqlalchemy.orm.interfaces import collections

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

# Sort
def sorted_nicely(l, key):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda item: [ convert(c) for c in re.split('([0-9]+)', key(item)) ]
    return sorted(l, key = alphanum_key)

# filter query by type
def filter_query(request, metric_object_type):
    search_params = {}
    numeric_filters = {}
    categorical_filters = {}

    categorical_filters, numeric_filters, search_params = separate_filter_types(request)

    metrics_query = DBSession.query(metric_object_type).order_by(metric_object_type.archive_id.desc())

    for filter_column, value in numeric_filters.items():
        if value[0]:
            metrics_query = metrics_query.filter(metric_object_type.get_column(filter_column[1]) >= int(value[0]))
        if value[1]:
            metrics_query = metrics_query.filter(metric_object_type.get_column(filter_column[1]) <= int(value[1]))

    for key, value in categorical_filters.items():
        if key == 'Chip Type':
            metrics_query = metrics_query.filter(metric_object_type.get_column(key) == value[:3])
            if len(value.decode('utf-8')) > 3:
                if value[3:] == " V2":
                    metrics_query = metrics_query.filter(metric_object_type.get_column("Gain") >= 0.65)
                else:
                    metrics_query = metrics_query.filter(metric_object_type.get_column("Gain") < 0.65)
        else:
            metrics_query = metrics_query.filter(metric_object_type.get_column(key) == value)

    sorted_numeric_filter_list = sorted_nicely(numeric_filters.keys(), itemgetter(0))

    ordered_numeric_filters = collections.OrderedDict()

    for keys in sorted_numeric_filter_list:
        ordered_numeric_filters[keys] = numeric_filters[keys]

    numeric_filters = OrderedDict()

    for keys, values in ordered_numeric_filters.items():
        numeric_filters[keys[0]] = (keys[1], values[0], values[1])

    return metrics_query, search_params, numeric_filters, categorical_filters

# Separate filter types
def separate_filter_types(request):

    numeric_filter_re = re.compile('metric_type_filter\d+')
    numeric_filter_re2 = re.compile('.*_number\d+')

    search_params = {}
    numeric_filters = {}
    categorical_filters = {}

    # clean up search parameters by eliminating empty searches
    for key in request.params.keys():
        if request.params[key].strip():
            search_params[key] = request.params[key].strip()

    # separate numeric parameters with their respective numeric value
    for key, value in search_params.items():
        if numeric_filter_re.match(key):
            category = numeric_filter_re.match(key).group()
            category_number = re.findall('\d+', category)
            min_number = 'min_number' + category_number[0]
            max_number = 'max_number' + category_number[0]

            if min_number in search_params and max_number in search_params:
                numeric_filters[(key, value)] = (search_params[min_number], search_params[max_number])
            elif min_number in search_params and max_number not in search_params:
                numeric_filters[(key, value)] = (search_params[min_number], '')
            elif min_number not in search_params and max_number in search_params:
                numeric_filters[(key, value)] = ('', search_params[max_number])

    # separate categorical parameters
    # except the ones needed for csrf verification and csv support 
    for key, value in search_params.items():
        if not numeric_filter_re.match(key) and not numeric_filter_re2.match(key) and key != 'extra_filter_number' and key != 'show_hide' and key != 'csrf_token' and key != 'metric_type':
            categorical_filters[key] = value

    for keys, value in request.params.items():
        search_params[keys] = value

    if 'extra_filter_number' not in search_params:
        search_params['extra_filter_number'] = u'0'

    return categorical_filters, numeric_filters, search_params

# Author: Anthony Rodriguez
@view_config(route_name='analysis_proton', renderer='analysis.mako', permission='view')
def analysis_proton(request):

    metrics_query, search_params, numeric_filters, categorical_filters = filter_query(request, MetricsProton)

    show_hide_defaults = {}
    for columns in MetricsProton.ordered_columns:
        show_hide_defaults[columns[1]] = "true"

    show_hide_defaults_ordered = OrderedDict(sorted(show_hide_defaults.items(), key=lambda t: t[0]))

    show_hide_false = {}
    for columns in MetricsProton.ordered_columns:
        show_hide_false[columns[1]] = "false"

    show_hide_false_ordered = OrderedDict(sorted(show_hide_false.items(), key=lambda t: t[0]))

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

    return {'metrics': metric_pages, 'pages': pages, 'page_url': page_url, "search": search_params, "metric_object_type": MetricsProton,
            "show_hide_defaults": json.dumps(show_hide_defaults_ordered), "show_hide_false": json.dumps(show_hide_false_ordered),
            "metric_columns": json.dumps(MetricsProton.numeric_columns), "numeric_filters_json": json.dumps(numeric_filters),
            'categorical_filters_json': json.dumps(categorical_filters)}

# Author: Anthony Rodriguez
@view_config(route_name="analysis_pgm", renderer="analysis.mako", permission="view")
def analysis_pgm(request):

    metrics_query, search_params, numeric_filters, categorical_filters = filter_query(request, MetricsPGM)

    show_hide_defaults = {}
    for columns in MetricsPGM.ordered_columns:
        show_hide_defaults[columns[1]] = "true"

    show_hide_defaults_ordered = OrderedDict(sorted(show_hide_defaults.items(), key=lambda t: t[0]))

    show_hide_false = {}
    for columns in MetricsPGM.ordered_columns:
        show_hide_false[columns[1]] = "false"

    show_hide_false_ordered = OrderedDict(sorted(show_hide_false.items(), key=lambda t: t[0]))

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

    return {'metrics': metric_pages, 'pages': pages, 'page_url': page_url, "search": search_params, "metric_object_type": MetricsPGM,
            "show_hide_defaults": json.dumps(show_hide_defaults_ordered), "show_hide_false": json.dumps(show_hide_false_ordered),
            "metric_columns": json.dumps(MetricsPGM.numeric_columns), "numeric_filters_json": json.dumps(numeric_filters),
            'categorical_filters_json': json.dumps(categorical_filters)}

#Author: Anthony Rodriguez
@view_config(route_name="analysis_show_hide", renderer="json", permission="view", xhr=True)
def show_hide_columns(request):

    show_hide_columns = {}

    request_path = request.params.get("metric_type")

    if request_path == '/analysis/pgm':
        if "show_hide_columns/analysis/pgm" in request.POST and request.POST['show_hide_columns/analysis/pgm']:
            show_hide_columns = request.params.get("show_hide_columns/analysis/pgm")
    elif request_path == '/analysis/proton':
        if "show_hide_columns/analysis/proton" in request.POST and request.POST['show_hide_columns/analysis/proton']:
            show_hide_columns = request.params.get("show_hide_columns/analysis/proton")

    if request_path == '/analysis/pgm':
        request.session["show_hide_session/analysis/pgm"]= show_hide_columns
    elif request_path == '/analysis/proton':
        request.session["show_hide_session/analysis/proton"]= show_hide_columns

    return {"columns": show_hide_columns}

# Author: Anthony Rodriguez
@view_config(route_name="analysis_csv", permission="view")
def analysis_csv(request):

    if request.params.get("metric_type", u'') == '/analysis/pgm':
        metric_object_type = MetricsPGM
    elif request.params.get("metric_type", u'') == '/analysis/proton':
        metric_object_type = MetricsProton

    show_hide = {}

    if "show_hide" in request.params and request.params['show_hide']:
        show_hide = json.loads(request.params.get('show_hide'))

    metrics_query, search_params, numeric_filters, categorical_filters = filter_query(request, metric_object_type)

    return Response(make_csv(metrics_query, metric_object_type, show_hide), content_type="text/csv", content_disposition="attachment; filename=analysis.csv")
