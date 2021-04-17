from django import forms

from reports.values import TRI_STATE_VERBAL


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
    is_known_good = forms.CharField(
        label="Known Disposition?",
        initial=None,
        widget=forms.RadioSelect(
            choices=TRI_STATE_VERBAL,
            attrs={"class": "disposition-radio"},
        ),
    )
    taser_ticket_number = forms.IntegerField(
        label="TASER Ticket Number", required=False, min_value=0
    )
    doc_file = forms.FileField(label="Select file", required=True)
    upload_another = forms.CharField(initial="no", widget=forms.HiddenInput)
