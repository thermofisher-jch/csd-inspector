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

from lemontest.models import SavedFilters
from lemontest.models import FileProgress
from lemontest.models import Graph
from lemontest.models import MetricReport
from lemontest.models import DBSession
from lemontest.models import Archive
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


@view_config(context=Exception)
def error_view(exc, request):
    logger.exception("Uncaught Exception:")
    return Response("Sorry, there was an error.", 500)


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


def rerun_diagnostics(archive):
    archive_id = archive.id
    archive.delete_tests()
    archive.diagnostics = upload.get_diagnostics(archive.archive_type)
    DBSession.flush()
    jobs = upload.make_diagnostic_jobs(archive, testers)
    transaction.commit()
    upload.run_diagnostics(archive_id, jobs)


@view_config(route_name="rerun", request_method="POST", permission='view')
def rerun_archive(request):
    archive_id = int(request.matchdict["archive_id"])
    archive = DBSession.query(Archive).options(subqueryload(
        Archive.diagnostics)).filter(Archive.id == archive_id).first()
    rerun_diagnostics(archive)
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

@view_config(route_name="old_browser", renderer="old_browser.mako", permission='view')
def old_browser(request):
    return {}


'''
    Task: create filter object that defines metric data set
    @param     request:           client/server request.params
    @param     metric_type:       metric object type for request type. If this is not set, the request should have metric_type in request.params
    @return    filter_obj:        filter object that defines metric data set
    @return    saved_filters:     saved filters in DB
    @return    extra_params:      GET and POST parameters not already used
    @return    sort_by_column:    currently sorted by column
'''
def get_db_queries(request, metric_type=None):
    '''validate request parameters'''
    categorical_filters, numeric_filters, sort_by_column, extra_params = validate_filter_params(request)

    '''make sure we have metric_type'''
    if not metric_type:
        if 'metric_type' not in extra_params or not extra_params['metric_type']:
            return HTTPInternalServerError()
        else:
            metric_type = extra_params['metric_type']

    '''
        if request is for an existing saved filter, query DB and return that filter
        else we make a temporary one, or return a not_found flag to client.
        not_found flag occurs when user tries to access a filter that does not exist in DB.
        filterid could be set to blank if user tries to save an empty filter set
       '''
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

    '''gets all saved filters from DB'''
    saved_filters = DBSession.query(SavedFilters).filter(SavedFilters.metric_type == metric_type).filter(SavedFilters.type != "temp").order_by(SavedFilters.id.desc())

    return filter_obj, saved_filters, extra_params, sort_by_column

'''
    Task: validates filters from request.params
    @param     request:                client/server request.params
    @param     params_only             called internally by other views directly, returns only extra_params
    @return    categorical_filters:    categorical component of current filter that will be applied to data set
    @return    numeric_filters:        numerical component of current filter that will be applied to data set
    @return    sort_by_column:         current column that data set will be sorted by
    @return    extra_params:           GET and POST parameters not already used
'''
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

    '''things to return at the end of validation'''
    extra_params = {}
    search_params = {}
    numeric_filters = {}
    categorical_filters = {}
    sort_by_column = {}

    '''grab only non-empty parameters'''
    for key in request.keys():
        if request[key].strip():
            search_params[key] = request[key].strip()

    '''
        find all parameters for numeric filters
        structure them effectively for the client side
        remove them from search_params after use
    '''
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
            extra_params[key] = value.replace(',', '')
            search_params[key] = ''

    '''find and remove all numeric filter stragglers
    that result from incomplete numeric filter forms'''
    for key in search_params.keys():
        if numeric_filter_re2.match(key):
            search_params[key] = ''

    '''look for all required parameters and set to default value if not found'''
    for param, default_value in required_params.items():
        if param not in search_params:
            extra_params[param] = default_value
        else:
            extra_params[param] = search_params[param]
            search_params[param] = ''

    '''needed parameter for numeric filters'''
    numeric_filters['extra_filters'] = extra_params['extra_filters_template']

    '''separate all non filter parameters out'''
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


'''BEGIN PLOT SUPPORT'''
'''
    Task: creates report object,
          creates two graph objects and assigns them to newly created report object,
          starts celery task to fill graph objects, and statistical data for report
    @return    HTTPFound    redirect to show_report view
'''
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

'''
    Task: divide customization parameters by plot type,
          start celery task to adjust each graph specifications
    @return    HTTPFound    redirect to show_report view
'''
@view_config(route_name='trace_customize_report', renderer='json', permission='view')
def customize_report(request):
    report_custom_re = re.compile('boxplot_.*')
    report_custom_re2 = re.compile('histogram_.*')

    boxplot_specs = {}
    histogram_specs = {}

    extra_params = validate_filter_params(request.params, params_only=True)

    '''divide parameters to corresponding graph'''
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

    '''
        if the report requested does not exist anymore for some reason,
        send back a not_found status and redirect to index page
    '''
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

'''
    Task: Reports page
    @return    status            found || not found if report object exists in the DB
    @return    report            report object
    @return    filter_obj:       filter object
    @return    filter_params:    formatted filter parameters that created the metric data set
    @return    url:              the URL to redirect to if the report was not found
'''
@view_config(route_name='trace_show_report', renderer='trace.report.mako', permission='view')
def show_report(request):
    numeric_filter_re = re.compile('metric_type_filter\d+')

    '''check if report parameter exists, and if not throw an error'''
    if "report" not in request.params or not request.params['report']:
        return HTTPInternalServerError()
    else:
        report_id = request.params['report']

    report = DBSession.query(MetricReport).filter(MetricReport.id == report_id).first()

    '''if specified report object does not exist in the DB, we send back status and redirect to index'''
    if not report:
        return {'status': 'not_found', 'url': request.route_path('index')}

    filter_obj = DBSession.query(SavedFilters).filter(SavedFilters.id == report.filter_id).first()

    '''format filter parameters used in the metric data set used to generate the report'''
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

'''
    Task: checks status of report, and sends back that status to client page
    @return    status:       found || not_found || error if report was found or not, or error
    @return    data:         if status == 'done' the formatted data needed to fill reports page
    @return    report_id:    if found, but status not done, the report id
'''
@view_config(route_name='trace_check_report_update', renderer='json', permission='view')
def check_report_update(request):
    extra_params = validate_filter_params(request.params, params_only=True)

    if 'report_id' not in extra_params or not extra_params['report_id']:
        return {'status': 'error'}

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

'''
    Task: checks status and progress indicator of FileProgress object, and sends it back to client
    @return    status:             error || pending || done depending on FileProgress object status
    @return    fileprogress_id:    id of FileProgress object
    @return    progress:           progress of FileProgress object
    @return    message:            error message if one exists
'''
@view_config(route_name='trace_check_file_update', renderer='json', permission='view')
def check_file_update(request):
    file_pending_re = re.compile('file_pending.*')

    extra_params = validate_filter_params(request.params, params_only=True)

    '''if for some reason we loose the progress id, we send back an error and clear user session'''
    if 'fileprogress_id' not in extra_params or not extra_params['fileprogress_id']:
        for key in request.session.keys():
            if file_pending_re.match(key):
                request.session[key] = ''
        return {'status': 'error'}
    if 'metric_type' not in extra_params or not extra_params['metric_type']:
        for key in request.session.keys():
            if file_pending_re.match(key):
                request.session[key] = ''
        return {'status': 'error'}

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

'''
    Task: stores the user preference for which columns are shown or hidden in the user session
'''
@view_config(route_name="trace_show_hide", renderer="json", permission="view", xhr=True)
def show_hide_columns(request):

    show_hide_columns = {}

    metric_type = request.params.get("metric_type")

    show_hide = "show_hide_columns_" + metric_type

    if show_hide in request.POST and request.POST[show_hide]:
        show_hide_columns = request.params.get(show_hide)

    request.session['show_hide_session_' + metric_type] = show_hide_columns

    return {"status": 200}

'''
    Task: reloads the same page with filterid applied
    @return    HTTPFound    redirect to same page with the added filterid parameter that matches the applied filter
'''
@view_config(route_name='trace_apply_filter', renderer="json", permission='view')
def apply_filter(request):
    '''checks if needed parameters are available, if not throws internal server error'''
    if 'metric_type' in request.params and request.params['metric_type'] and 'filterid' in request.params and request.params['filterid']:
        metric_type = request.params['metric_type']
        filter_id = request.params['filterid']
    else:
        return HTTPInternalServerError()

    '''sets redirect variable'''
    url = request.route_url('trace_' + metric_type)
    url += '?filterid=' + filter_id

    return HTTPFound(location=url)

'''
    Task: saved given filter as a DB object
    @return    HTTPFound    redirect to same page with the added filterid parameter that matches the saved and now applied filter
'''
@view_config(route_name="trace_save_filter", renderer="json", permission="view")
def save_filter(request):

    filter_obj, saved_filters, extra_params, sort_column = get_db_queries(request.params)

    if 'metric_type' not in extra_params or not extra_params['metric_type']:
        return HTTPInternalServerError()
    else:
        metric_type = extra_params['metric_type']

    url = request.route_url('trace_' + metric_type)

    '''if the filter object is not empty, we redirect to filter applied; else we send back blank flag to UI'''
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

'''
    Task: deletes given filter object from DB
    @return    HTTPFound    redirect to same page
'''
@view_config(route_name='trace_delete_saved_filter', renderer='json', permission='view')
def delete_saved_filter(request):
    filter_id = request.params.get('filter_to_delete', '')
    filter_type = request.params.get('metric_type', '')

    if filter_id:
        filter = DBSession.query(SavedFilters).filter(SavedFilters.id == filter_id).first()
        DBSession.delete(filter)
        transaction.commit()

        url = request.route_url('trace_' + filter_type)

    return HTTPFound(location=url)

'''DEBUG DB'''
''' Task: view all objects in the DB in neat tables in their own page comment out this line with a # to activate
@view_config(route_name='db_query', renderer='db_objects.mako', permission='view')
def db_query(request):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

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

comment out this line with a # to activate'''
'''END DEBUG DB'''
