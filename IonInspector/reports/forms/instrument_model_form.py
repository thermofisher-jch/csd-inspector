import django.forms as forms
from crispy_forms.bootstrap import UneditableField, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from django.urls import reverse

from reports.models import Instrument


class InstrumentModelForm(forms.ModelForm):
    class Meta:
        model = Instrument
        fields = (
            "serial_number",
            "instrument_name",
            "site",
            "fas",
            "fbs",
            "fse",
        )
        ignored = ("serial_number", "instrument_name")

    def __init__(self, *args, **kwargs):
        super(InstrumentModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "POST"
        self.helper.form_action = reverse(
            "instrument-detail", args=[kwargs["instance"].id]
        )
        self.helper.form_class = "form-horizontal"
        self.helper.form_tag = True
        self.helper.form_id = "instrument-form"
        self.helper.formset_error_title = "Errors"
        self.helper.template = "bootstrap3/whole_uni_form.html"
        self.helper.layout = Layout(
            Field("serial_number", readonly=True),
            Field("instrument_name", readonly=True),
            "site",
            "fas",
            "fbs",
            "fse",
            FormActions(
                Submit("submit", "Save"),
            ),
        )
