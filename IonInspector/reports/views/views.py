import json
import logging
import os
import datetime
import pytz

from dateutil.parser import parse as date_parse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models.fields.files import FieldFile
from django.shortcuts import render, HttpResponseRedirect
from django.utils import timezone
from django_tables2 import RequestConfig

from reports.api import ArchiveResource
from reports.forms import SingleArchiveUploadForm
from reports.models import Archive
from reports.tables import ArchiveTable
from reports.values import PGM_RUN, CATEGORY_CHOICES, ARCHIVE_TYPES
from reports.utils import get_file_path, get_serialized_model, Unnest

logger = logging.getLogger(__name__)


def index(request):
    """
    Landing page request
    :param request:
    :return:
    """

    ctx = dict({})
    return render(request, "index.html", context=ctx)


def upload(request):
    """
    Upload an archive request
    :param request:
    :return:
    """

    # Handle file upload
    if request.method == "POST":
        form = SingleArchiveUploadForm(data=request.POST, files=request.FILES)
        archive = Archive(
            identifier=form.data["archive_identifier"],
            site=form.data["site_name"],
            time=timezone.now(),
            submitter_name=form.data["name"],
            is_known_good=form.data["is_known_good"],
            taser_ticket_number=int(form.data["taser_ticket_number"])
            if form.data["taser_ticket_number"]
            else None,
        )
        # perform a save here in order to assert that we have a pk for this entry, otherwise we can't get a directory
        # on the file system to save the doc_file or results too.
        archive.save()

        # save the file against since we will need an id in order to create the save path
        archive.doc_file = request.FILES["doc_file"]
        archive.save()

        archive.archive_type = archive.detect_archive_type()
        archive.save()

        try:
            # fire off the diagnostics in the background automatically
            archive.execute_diagnostics()
        except Exception as exc:
            logger.exception("Error starting execute_diagnostics")
            # if we get an exception we need to remove the database entry and folder since it was invalid
            archive.delete()

            # render a error response
            ctx = dict({"error_msg": exc.message})
            return render(request, "error.html", context=ctx)

        # Redirect to new document's detail view after POST if "Upload Archive" was selected
        if form.data["upload_another"] != "yes":
            return HttpResponseRedirect(reverse("report", args=[archive.pk]))
        else:
            new_form = SingleArchiveUploadForm(
                data=request.POST.copy(), files=request.FILES
            )
            new_form.data["upload_another"] = "no"
            ctx = dict({"form": new_form})
            return render(request, "upload.html", context=ctx)
    else:
        form = SingleArchiveUploadForm()

    ctx = dict({"form": form})
    return render(request, "upload.html", context=ctx)


def reports(request):
    """
    List all of the reports
    :param request:
    :return:
    """
    site_search = ""
    submitter_name_search = ""
    archive_type_search = ""
    identifier_search = ""
    taser_ticket_number_search = ""
    is_known_good_search = []
    date_start_search = ""
    date_end_search = ""
    tags_search = ""

    archives = Archive.objects.order_by("time")
    if request.GET.get("site", ""):
        site_search = request.GET["site"]
        archives = archives.filter(site__icontains=site_search)
    if request.GET.get("submitter_name", ""):
        submitter_name_search = request.GET["submitter_name"]
        archives = archives.filter(submitter_name__icontains=submitter_name_search)
    if request.GET.get("archive_type", ""):
        archive_type_search = request.GET["archive_type"]
        archives = archives.filter(archive_type=archive_type_search)
    if request.GET.get("identifier", ""):
        identifier_search = request.GET["identifier"]
        archives = archives.filter(identifier__icontains=identifier_search)
    if request.GET.get("inst_serial", ""):
        identifier_search = request.GET["inst_serial"]
        archives = archives.filter(identifier__icontains=identifier_search)
    if request.GET.get("taser_ticket_number_name", ""):
        taser_ticket_number_search = request.GET["taser_ticket_number_name"]
        archives = archives.filter(taser_ticket_number=int(taser_ticket_number_search))
    if request.GET.get("tags", ""):
        tags_search = request.GET.getlist("tags")
        archives = archives.filter(search_tags__contains=tags_search)
    if request.GET.get("is_known_good"):
        is_known_good_search = request.GET.getlist("is_known_good")
        archives = archives.filter(is_known_good__in=is_known_good_search)
    if request.GET.get("date_start", ""):
        date_start_search = request.GET["date_start"]
    if request.GET.get("date_end", ""):
        date_end_search = request.GET["date_end"]

    if date_start_search:
        date_start = date_parse(date_start_search)
        if date_start:
            archives = archives.filter(time__gt=date_start)

    if date_end_search:
        date_end = date_parse(date_end_search)
        if date_end:
            archives = archives.filter(time__lt=date_end)

    table = ArchiveTable(archives.with_taser_ticket_url(), order_by="-time")
    table.paginate(page=request.GET.get("page", 1), per_page=100)
    RequestConfig(request).configure(table)

    available_tags = sorted(
        Archive.objects.annotate(unnested_tags=Unnest("search_tags"))
        .values_list("unnested_tags", flat=True)
        .distinct()
    )

    ctx = dict(
        {
            "archives": table,
            "archive_types": ARCHIVE_TYPES,
            "site_search": site_search,
            "submitter_name_search": submitter_name_search,
            "archive_type_search": archive_type_search,
            "identifier_search": identifier_search,
            "taser_ticket_number_search": taser_ticket_number_search,
            "include_known_good": "selected=" if "T" in is_known_good_search else "",
            "include_known_issues": "selected=" if "F" in is_known_good_search else "",
            "include_unknown": "selected=" if "K" in is_known_good_search else "",
            "date_start_search": date_start_search,
            "date_end_search": date_end_search,
            "tags_search": tags_search,
            "available_tags": available_tags,
            "template_name": "tables/reports.html",
        }
    )
    return render(request, "reports.html", context=ctx)


def report(request, pk):
    """
    Render the report archive page
    :param request:
    :param pk: Primary key of the archive to render
    :return:
    """

    archive = Archive.objects.get(pk=pk)
    diagnostics = archive.diagnostics.order_by("name")

    first_diagnostic = diagnostics.order_by("start_execute").first()
    start_time = (
        first_diagnostic.start_execute if first_diagnostic is not None else None
    )

    thumbnail_pdf_present = False
    full_pdf_present = False
    try:
        thumbnail_pdf_present = os.path.exists(
            os.path.join(archive.archive_root, "report.pdf")
        )
    except ValueError:
        pass

    if archive.archive_type != PGM_RUN:
        try:
            full_pdf_present = os.path.exists(
                os.path.join(archive.archive_root, "full_report.pdf")
            )
        except ValueError:
            pass

    relative_coverage_analysis_path = (
        "archive_files/" + str(pk) + "/coverageAnalysis/coverageAnalysis.html"
    )
    PST = pytz.timezone("US/Pacific")

    ctx = dict(
        {
            "archive_type_choices_json": json.dumps(
                [
                    {"name": k, "value": v}
                    for v, k in archive._meta.get_field("archive_type").choices
                ]
            ),
            # dump twice to make it a js string containing json
            "diagnostic_category_choices_json": json.dumps(
                json.dumps(CATEGORY_CHOICES)
            ),
            "archive": archive,
            "archive_time": archive.time.astimezone(PST).strftime("%d %b %Y, %I:%M %p %Z"),
            "archive_type": archive.archive_type,
            "diagnostics": diagnostics,
            "thumbnail_pdf_present": thumbnail_pdf_present,
            "full_pdf_present": full_pdf_present,
            # dump twice to make it a js string containing json
            "api_resource": json.dumps(get_serialized_model(archive, ArchiveResource)),
            "coverage_analysis_path": settings.MEDIA_URL
            + relative_coverage_analysis_path
            if os.path.exists(
                os.path.join(settings.MEDIA_ROOT, relative_coverage_analysis_path)
            )
            else "",
            "start_time": start_time.astimezone(PST).strftime("%d %b %Y, %I:%M %p %Z"),
            "is_sequencer": json.dumps(archive.is_sequencer()),
        }
    )
    return render(request, "report.html", ctx)


def readme(request, diagnostic_name):
    """
    Get the diagnostic readme
    :param request:
    :param diagnostic_name:
    :return:
    """

    contents = open(
        os.path.join(
            settings.SITE_ROOT,
            "IonInspector",
            "reports",
            "diagnostics",
            diagnostic_name,
            "README",
        )
    ).read()
    ctx = dict({"readme": contents})
    return render(request, "readme.html", ctx)
