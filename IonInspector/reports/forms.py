from django import forms
from reports.models import TEST_MANIFEST


class ArchiveForm(forms.Form):
    """
    Form for uploading a document
    """

    name = forms.CharField(label='Your Name', required=True)
    site_name = forms.CharField(label='Site Name', required=True)
    archive_identifier = forms.CharField(label='Archive Identifier', required=True)
    archive_type = forms.ChoiceField(label='Archive Type', required=True, choices=[device.replace("_", " ") for device in TEST_MANIFEST.keys()])
    doc_file = forms.FileField(label='Select file', required=True)
