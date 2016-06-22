from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render_to_response, HttpResponseRedirect
from IonInspector.forms import ArchiveForm
from IonInspector.models import Archive, TEST_MANIFEST
from datetime import datetime
from IonInspector.tables import ArchiveTable
from django_tables2 import RequestConfig
import os


def index(request):
    """
    Landing page request
    :param request:
    :return:
    """

    ctx = RequestContext(request, {})
    return render_to_response("index.html", context_instance=ctx)


def upload(request):
    """
    Upload an archive request
    :param request:
    :return:
    """

    # Handle file upload
    if request.method == 'POST':
        form = ArchiveForm(data=request.POST, files=request.FILES)

        archive = Archive(
            label=form.data['archive_label'],
            site=form.data['site_name'],
            time=datetime.utcnow(),
            submitter_name=form.data['name'],
            archive_type=form.data['archive_type'].replace(" ", "_"),
        )
        # perform a save here in order to assert that we have a pk for this entry, otherwise we can't get a directory
        # on the file system to save the doc_file or results too.
        archive.save()

        # save the file second since we will need an id
        archive.doc_file = request.FILES['doc_file']
        archive.save()

        # fire off the diagnostics in the background automatically
        archive.execute_diagnostics()

        # Redirect to the document list after POST
        return HttpResponseRedirect(reverse('IonInspector.views.report', args=[archive.pk]))
    else:
        form = ArchiveForm()

    ctx = RequestContext(request, {'form': form})
    return render_to_response("upload.html", context_instance=ctx)


def reports(request):
    """
    List all of the reports
    :param request:
    :return:
    """

    archive_types = TEST_MANIFEST.keys()

    table = ArchiveTable(Archive.objects.all())
    RequestConfig(request).configure(table)
    ctx = RequestContext(request, {'archives': table, 'archive_types': archive_types})
    return render_to_response("reports.html", context_instance=ctx)


def report(request, pk):
    """
    Render the report archive page
    :param request:
    :param pk: Primary key of the archive to render
    :return:
    """

    archive = Archive.objects.get(pk=pk)

    ctx = RequestContext(request, {'archive': archive})
    return render_to_response("report.html", ctx)


def documentation(request):
    """
    Render documentation page
    :param request:
    :return:
    """

    return render_to_response("documentation.html")


def readme(request, diagnostic_name):
    """
    Get the diagnostic readme
    :param request:
    :param diagnostic_name:
    :return:
    """

    contents = open(os.path.join(settings.SITE_ROOT, 'lemontest', 'diagnostics', diagnostic_name, 'README')).read()
    return render_to_response("readme.html", {'readme': contents})
