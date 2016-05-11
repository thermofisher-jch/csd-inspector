from django import forms
from django.conf import settings


class ArchiveForm(forms.Form):
    """
    Form for uploading a document
    """

    name = forms.CharField(label='Your Name', required=True)
    site_name = forms.CharField(label='Site Name', required=True)
    archive_label = forms.CharField(label='Archive Label', required=True)
    archive_type = forms.ChoiceField(label='Archive Type', required=True, choices=[device.replace("_", " ") for device in settings.TEST_MANIFEST.keys()])
    doc_file = forms.FileField(label='Select file', required=True)
