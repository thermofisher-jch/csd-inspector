from base64 import b64encode

from django.http import JsonResponse

from reports.forms import CaptureArchiveHashesForm
from reports.models import Archive


def hash_archive(request):
    """
    Capture hashes for a previously uploaded archive by running it through the NGinx upload plugin and allowing
    it to compute hashes while stripping the file's data out of teh request.  Server backend only sees requests
    containing hashes paired with an archive idenitifier.  Allow Nginx to cleanup its staged copy of the file as
    we already have stored original copy.

    :param request: A Django HTTP Request
    :return: JSON response
    """

    # Handle file upload
    if request.method == "POST":
        # Rewrite nginx-derived query form field names to account for '.' being
        # an invalid character in a python variable name by applying a field name transformation
        # that replaces those .'s with underscores.
        form = CaptureArchiveHashesForm(data=request.POST, files=request.FILES)
        archive = Archive.objects.get(form.data["id"])
        archive.sha1_hash = b64encode(form.data["doc_file_sha1"].decode("hex"))[
            :27
        ]  # Strips one trailing =
        archive.md5_hash = b64encode(form.data["doc_file_md5"].decode("hex"))[
            :22
        ]  # Strips two trailing ==
        archive.crc32_sum = b64encode(form.data["doc_file_crc32"].decode("hex"))[
            :6
        ]  # Strips two trailing ==
        archive.save()

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
