import os
import shutil
from base64 import b64encode

from django.conf import settings
from django.http import JsonResponse
from django.db.models.fields.files import FieldFile
from django.utils import timezone

from reports.forms import BatchArchiveUploadForm
from reports.models import Archive
from reports.utils import get_file_path


def batch_upload(request):
    """
    Complete import of an archive upload request already staged by NGINX filtering reverse proxy
    :param request: A Django HTTP Request
    :return: JSON response
    """

    # Handle file upload
    if request.method == "POST":
        # Rewrite nginx-derived query form field names to account for '.' being
        # an invalid character in a python variable name by applying a field name transformation
        # that replaces those .'s with underscores.
        form = BatchArchiveUploadForm(data=request.POST, files=request.FILES)
        archive = Archive(
            identifier=form.data["archive_identifier"],
            site=form.data["site_name"],
            time=timezone.now(),
            submitter_name=form.data["name"],
            is_known_good=form.data["is_known_good"],
            taser_ticket_number=int(form.data["taser_ticket_number"])
            if "taser_ticket_number" in form.data
            else None,
            sha1_hash=b64encode(form.data["doc_file_sha1"].decode("hex"))[
                :27
            ],  # Strips one trailing =
            md5_hash=b64encode(form.data["doc_file_md5"].decode("hex"))[
                :22
            ],  # Strips two trailing ==
            crc32_sum=b64encode(form.data["doc_file_crc32"].decode("hex"))[
                :6
            ],  # Strips two trailing ==
        )
        # perform a save here in order to assert that we have a pk for this entry, otherwise we can't get a directory
        # on the file system to save the doc_file or results to.
        archive.save()

        success = False
        try:
            # Move the temporary upload from where nginx placed it to where we expect it to live for the long term, and
            # restore its original file name at the same time, then stash the portion of the permanent file path in
            # Django's FileField wrapper so we can attach it to the Archive model and save it with this change.  We
            # have to do this rename rather than just pass the file path as created by nginx because the archive
            # origin device detection logic in large part relies upon the arhive having its original filename
            relative_file_path = get_file_path(archive, form.data["doc_file_source_name"])
            new_file_path = os.path.join(settings.MEDIA_ROOT, relative_file_path)
            shutil.move(form.data["doc_file_path_saved"], new_file_path)
            archive.doc_file = FieldFile(archive, Archive.doc_file.field, relative_file_path)
            archive.save()
            archive.archive_type = archive.detect_archive_type()
            archive.save()
            archive.execute_diagnostics()
            success = True
        finally:
            if not success:
                archive.delete()
        return JsonResponse(
            {
                "status": "success",
                "id": archive.id,
                "doc_file": archive.doc_file.path,
                "archive_type": archive.archive_type,
                "archive_identifier": archive.identifier,
                "site_name": archive.site,
                "name": archive.submitter_name,
                "taser_ticket_number": archive.taser_ticket_number,
                "is_known_good": archive.is_known_good,
                "report_url": archive.get_absolute_url(),
                "sha1_hash": archive.sha1_hash,
                "md5_hash": archive.md5_hash,
                "crc32_sum": archive.crc32_sum,
            },
            safe=True,
        )
    # elif request.method == "GET":
    #     return render(request, "pages/batch_upload.html", {})

    raise NotImplementedError("Only POST is supported")
