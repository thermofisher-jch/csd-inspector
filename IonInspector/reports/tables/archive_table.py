import pytz
import django_tables2 as tables
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe, mark_for_escaping
from django_tables2.utils import A

from .width_attrs import width_attrs
from ..models import Archive


class ArchiveTable(tables.Table):
    """
    Table for rendering archives.
    """

    id = tables.LinkColumn(
        verbose_name="ID",
        attrs=width_attrs("32px"),
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
        attrs=width_attrs("25%"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("identifier"),
        empty_values=(None, ""),
    )
    site = tables.LinkColumn(
        verbose_name="Site",
        attrs=width_attrs("18%"),
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
        attrs=width_attrs("96px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("archive_type"),
        empty_values=("", "Unknown", None),
    )
    taser_ticket_url = tables.URLColumn(
        verbose_name="TASER",
        attrs=width_attrs("72px"),
        orderable=True,
        text=lambda archive: archive.taser_ticket_number,
        empty_values=("", None),
    )
    serial_number = tables.LinkColumn(
        verbose_name="Serial Number",
        attrs=width_attrs("6vw"),
        orderable=True,
        viewname="instrument-detail",
        args=[A("as_valkyrie__instrument")],
        accessor=A("as_valkyrie__instrument__serial_number"),
        empty_values=("", None),
    )
    is_known_good = tables.LinkColumn(
        verbose_name="Known Good?",
        attrs=width_attrs("88px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("is_known_good"),
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
        PST = pytz.timezone('US/Pacific')
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank'>%s</a>" % (
                reverse("report", args=[record.id]),
                value.astimezone(PST).strftime("%d %b %Y, %H:%M %p %Z")
            )
        )

    def render_search_tags(self, value, record):
        tags = "".join(
            [
                "<span class='label'>{}</span>".format(mark_for_escaping(x))
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
            "taser_ticket_url",
            "submitter_name",
            "time",
            "archive_type",
            "site",
            "is_known_good",
            "search_tags",
        )
        # exclude the summary column data
        exclude = (
            "doc_file",
            "taser_ticket_number",
            "serial_number",
            "summary",
            "failure_mode",
            "sha1_hash",
            "md5_hash",
            "crc32_sum"
        )
        show_header = True
        orderable = True
        order_by = "-date"
        empty_text = "No matches found"
        template_name = "tables/reports.html"
