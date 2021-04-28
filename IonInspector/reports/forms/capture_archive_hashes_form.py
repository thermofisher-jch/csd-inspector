import django.forms as forms

from reports.values import TRI_STATE_VERBAL


class CaptureArchiveHashesForm(forms.Form):
    """Form for uploading a document asynchronously with JSON response"""

    id = forms.IntegerField(required=True)
    doc_file_md5 = forms.CharField(required=True)
    doc_file_sha1 = forms.CharField(required=True)
    doc_file_size = forms.IntegerField(required=True)
    doc_file_crc32 = forms.CharField(required=True)
