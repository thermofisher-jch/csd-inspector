from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render_to_response, HttpResponseRedirect
from IonInspector.forms import ArchiveForm
from IonInspector.models import Archive
from datetime import datetime
from IonInspector.tables import ArchiveTable
from django_tables2   import RequestConfig

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

        try:
            valid = form.is_valid()
        except:
            valid = False

        if form.is_valid():
            archive = Archive(
                label=form.data['archive_label'],
                site=form.data['site_name'],
                time=datetime.utcnow(),
                submitter_name=form.data['name'],
                archive_type=form.data['archive_type'].replace(" ", "_"),
            )
            archive.save()

            # save the file second since we will need an id
            archive.docfile = request.FILES['docfile']
            archive.save()

            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('IonInspector.views.reports'))
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

    archive_types = settings.TEST_MANIFEST.keys()

    table = ArchiveTable(Archive.objects.all())
    RequestConfig(request).configure(table)
    ctx = RequestContext(request, {'archives': table, 'archive_types': archive_types})
    return render_to_response("reports.html", context_instance=ctx)