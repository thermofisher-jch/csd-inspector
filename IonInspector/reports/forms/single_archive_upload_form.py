from django import forms

from reports.forms.archive_upload_form import ArchiveUploadForm


class SingleArchiveUploadForm(ArchiveUploadForm):
    """Form for uploading a single document"""

    doc_file = forms.FileField(
        label="Select file",
        required=True,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    upload_another = forms.CharField(initial="no", widget=forms.HiddenInput)
