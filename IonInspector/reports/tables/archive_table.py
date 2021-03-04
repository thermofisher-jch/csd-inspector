import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django_tables2.utils import A

from reports.models import Archive
from .width_attrs import width_attrs


class ArchiveTable(tables.Table):
    """
    Table for rendering archives.
    """

    id = tables.LinkColumn(
        verbose_name="ID",
        attrs=width_attrs("60px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("id"),
        empty_values=(),
    )
    time = tables.DateTimeColumn(
        verbose_name="Date",
        attrs=width_attrs("160px"),
        orderable=True,
        accessor=A("time"),
        empty_values=(None,),
    )
    identifier = tables.LinkColumn(
        verbose_name="Label",
        attrs=width_attrs("30%"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("identifier"),
        empty_values=(None, ""),
    )
    site = tables.LinkColumn(
        verbose_name="Site",
        attrs=width_attrs("20%"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("site"),
        empty_values=(None, ""),
    )
    submitter_name = tables.LinkColumn(
        verbose_name="Submitter",
        attrs=width_attrs("15%"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("submitter_name"),
        empty_values=(None, ""),
    )
    archive_type = tables.LinkColumn(
        verbose_name="Type",
        attrs=width_attrs("100px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("archive_type"),
        empty_values=("", "Unknown", None),
    )
    taser_ticket_number = tables.URLColumn(
        verbose_name="TASER",
        attrs=width_attrs("80px"),
        orderable=True,
        empty_values=(0, "", None),
    )
    serial_number = tables.LinkColumn(
        verbose_name="Serial Number",
        attrs=width_attrs("6vw"),
        orderable=True,
        viewname="instrument-detail",
        args=[A("as_valkyrie__instrument")],
        accessor=A("as_valkyrie__instrument__serial_number"),
        empty_values=(None),
    )
    search_tags = tables.LinkColumn(
        verbose_name="Tags",
        attrs=width_attrs("200px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("search_tags"),
        empty_values=(list(), None),
    )

    def render_time(self, value, record):
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank'>%s</a>"
            % (reverse("report", args=[record.id]), naturaltime(value))
        )

    def render_search_tags(self, value, record):
        tags = "".join(
            [
                "<span class='label'>{}</span>".format(x)
                for x in value
                if ":" not in x
            ]
        )
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank' style='padding:7px'>%s</a>"
            % (reverse("report", args=[record.id]), tags)
        )

    class Meta:
        model = Archive
        per_page = 100
        attrs = {"class": "table table-striped table-hover", "id": "archive_table"}
        # setup the column sequence
        sequence = (
            "id",
            "identifier",
            "taser_ticket_number",
            "submitter_name",
            "time",
            "archive_type",
            "site",
            "search_tags",
        )
        # exclude the summary column data
        exclude = (
            "doc_file",
            "serial_number",
            "summary",
            "failure_mode",
            "is_baseline",
        )
        show_header = True
        orderable = True
        empty_text = "No matches found"
        template_name = "tables/reports.html"
