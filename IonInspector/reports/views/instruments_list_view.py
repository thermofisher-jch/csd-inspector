from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django_filters.views import FilterView, FilterMixin
from django_tables2 import SingleTableMixin, SingleTableView

from reports.models import Instrument
from reports.tables.instrument_list_table import InstrumentTable
from reports.filters import InstrumentListFilter


class InstrumentsListView(SingleTableMixin, FilterView):
    model = Instrument
    template_name = "pages/instruments_list.html"
    table_class = InstrumentTable
    filterset_class = InstrumentListFilter

    def get_context_data(self, **kwargs):
        filter_helper = FormHelper()
        kwargs["filter"].form.helper = filter_helper
        filter_helper.form_method = "GET"
        filter_helper.form_action = "instruments-list"
        filter_helper.form_class = "form-horizontal"
        filter_helper.form_tag = True
        filter_helper.form_id = "search-form"
        filter_helper.template = "bootstrap3/whole_uni_form.html"

        return super(InstrumentsListView, self).get_context_data(**kwargs)
