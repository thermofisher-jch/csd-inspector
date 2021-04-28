import django.forms as forms

from reports.forms.archive_upload_form import ArchiveUploadForm


class BatchArchiveUploadForm(ArchiveUploadForm):
    """Form for uploading a document asynchronously with JSON response"""

    doc_file_md5 = forms.CharField(required=True)
    doc_file_sha1 = forms.CharField(required=True)
    doc_file_size = forms.IntegerField(required=True)
    doc_file_crc32 = forms.CharField(required=True)
    doc_file_path_saved = forms.CharField(required=True)
    doc_file_source_name = forms.CharField(required=True)
