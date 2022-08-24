from crispy_forms.helper import FormHelper
from django.urls import reverse
from django.views.generic import UpdateView
from django_filters.views import FilterMixin
from django_tables2 import SingleTableMixin, RequestConfig

from reports.filters import InstrumentTrackerListFilter
from reports.forms import InstrumentModelForm
from reports.models import Instrument, Archive
from reports.tables import ArchiveTable


class InstrumentDetailView(SingleTableMixin, FilterMixin, UpdateView):
    model = Instrument
    template_name = "pages/instrument_detail.html"
    filterset_class = InstrumentTrackerListFilter
    form_class = InstrumentModelForm
    context_table_name = "table"

    def get_table(self):
        filterset = self.get_filterset(self.get_filterset_class())
        retval = ArchiveTable(filterset.qs.select_related())
        request_config = RequestConfig(self.request, True)
        request_config.configure(retval)
        return retval

    def get_filterset(self, clazz):
        kwargs = {
            "data": self.request.GET or None,
            "request": self.request,
            "queryset": Archive.objects.with_serial_number().filter(
            ),
        }
        return clazz(**kwargs)

    def get_context_data(self, filter=None, **kwargs):
        filter_helper = FormHelper()
        filter_helper.form_method = "GET"
        filter_helper.form_action = reverse(
            "instrument-detail", args=[self.kwargs["pk"]]
        )
        filter_helper.form_class = "form-horizontal"
        filter_helper.form_tag = True
        filter_helper.form_id = "search-form"
        filter_helper.template = "bootstrap3/whole_uni_form.html"
        if not "filter" in kwargs:
            kwargs["filter"] = self.get_filterset(self.get_filterset_class())
        kwargs["filter"].form.helper = filter_helper
        return super(InstrumentDetailView, self).get_context_data(**kwargs)
