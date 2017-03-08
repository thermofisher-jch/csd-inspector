from django import forms
from reports.models import TEST_MANIFEST


class ArchiveForm(forms.Form):
    """
    Form for uploading a document
    """

    name = forms.CharField(label='Your Name', required=True, widget=forms.TextInput(attrs={"autocomplete": "off"}))
    site_name = forms.CharField(label='Site Name', required=True, widget=forms.TextInput(attrs={"autocomplete": "off"}))
    archive_identifier = forms.CharField(label='Archive Identifier', required=True)
    archive_type = forms.ChoiceField(label='Archive Type', required=True, choices=[device.replace("_", " ") for device in TEST_MANIFEST.keys()])
    taser_ticket_number = forms.IntegerField(label='Taser Ticket Number', required=False, min_value=0)
    doc_file = forms.FileField(label='Select file', required=True)
