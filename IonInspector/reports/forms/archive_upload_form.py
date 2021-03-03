from django import forms


class ArchiveForm(forms.Form):
    """Form for uploading a document"""

    name = forms.CharField(
        label="Your Name",
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    site_name = forms.CharField(
        label="Site Name",
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    archive_identifier = forms.CharField(label="Archive Identifier", required=True)
    is_baseline = forms.BooleanField(label="Baseline?", initial=False, required=False)
    taser_ticket_number = forms.IntegerField(
        label="TASER Ticket Number", required=False, min_value=0
    )
    doc_file = forms.FileField(label="Select file", required=True)
    upload_another = forms.CharField(initial="no", widget=forms.HiddenInput)
