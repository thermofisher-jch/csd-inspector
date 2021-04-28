from abc import ABCMeta
from django import forms

from reports.values import TRI_STATE_VERBAL


class ArchiveUploadForm(forms.Form):
    """Form for uploading a document"""

    name = forms.CharField(
        label="Your Name",
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "off", "class": "form-control"}),
    )
    site_name = forms.CharField(
        label="Site Name",
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "off", "class": "form-control"}),
    )
    archive_identifier = forms.CharField(
        label="Archive Identifier",
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    is_known_good = forms.CharField(
        label="Known Disposition?",
        initial=None,
        widget=forms.RadioSelect(
            choices=TRI_STATE_VERBAL,
            attrs={"class": "disposition-radio"},
        ),
    )
    taser_ticket_number = forms.IntegerField(
        label="TASER Ticket Number",
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
