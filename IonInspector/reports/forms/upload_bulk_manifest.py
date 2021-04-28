from django import forms


class GenerateBulkManifest(forms.Form):
    """Form for uploading a document"""

    name = forms.CharField(
        label="Your Name",
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    site_name = forms.CharField(
        label="Folder Path",
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
