import django_tables2 as tables
from django_tables2.utils import A

from .width_attrs import width_attrs


class InstrumentTable(tables.Table):
    serial_number = tables.LinkColumn(
        accessor=A("serial_number"),
        orderable=True,
        attrs=width_attrs("20vw"),
        viewname="instrument-detail",
        args=[A("id")],
    )
    instrument_name = tables.LinkColumn(
        accessor=A("instrument_name"),
        orderable=True,
        attrs=width_attrs("20vw"),
        viewname="instrument-detail",
        args=[A("id")],
    )
    site = tables.LinkColumn(
        accessor=A("site"),
        orderable=True,
        attrs=width_attrs("40vw"),
        viewname="instrument-detail",
        args=[A("id")],
    )

    class Meta:
        show_header = True
        per_page = 25
        order_by = "serial_number"
        orderable = True
        empty_text = "No matching instruments found"
        attrs = {"class": "table table-striped table-hover", "id": "model-table"}
        template_name = "django_tables2/bootstrap.html"
