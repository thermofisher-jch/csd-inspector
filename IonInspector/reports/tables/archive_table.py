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
        attrs=width_attrs("140px"),
        orderable=True,
        accessor=A("time"),
        empty_values=(None,),
    )
    identifier = tables.LinkColumn(
        verbose_name="Label",
        attrs=width_attrs("100px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("identifier"),
        empty_values=(None, ""),
    )
    site = tables.LinkColumn(
        verbose_name="Site",
        attrs=width_attrs("100px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("site"),
        empty_values=(None, ""),
    )
    device_name = tables.LinkColumn(
        verbose_name="device_name",
        attrs=width_attrs("80px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("device_name"),
        empty_values=(None, ""),
    )
    submitter_name = tables.LinkColumn(
        verbose_name="Submitter",
        attrs=width_attrs("100px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("submitter_name"),
        empty_values=(None, ""),
    )
    archive_type = tables.LinkColumn(
        verbose_name="Type",
        attrs=width_attrs("70px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("archive_type"),
        empty_values=("", "Unknown", None),
    )
    taser_ticket_number_txt = tables.LinkColumn(
        verbose_name="TASER",
        attrs=width_attrs("40px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("taser_ticket_number_txt"),
        empty_values=("", None),
    )
    serial_number = tables.LinkColumn(
        verbose_name="Serial Number",
        attrs=width_attrs("100px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("serial_number"),
        empty_values=("", None),
    )
    is_known_good = tables.LinkColumn(
        verbose_name="Known Good?",
        attrs=width_attrs("30px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("is_known_good"),
    )
    loading_density = tables.TemplateColumn(
        verbose_name="Loading",
        attrs=width_attrs("80px"),
        orderable=False,
        accessor=A("loading_density"),
        template_name="partials/loading_density_thumbnail.html",
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
    summary = tables.LinkColumn(
        verbose_name="Summary",
        attrs=width_attrs("200px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("summary"),
        empty_values=(list(), None),
    )
    failure_mode = tables.LinkColumn(
        verbose_name="Failure",
        attrs=width_attrs("200px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("failure_mode"),
        empty_values=(list(), None),
    )
    loading_percent = tables.LinkColumn(
        verbose_name="LoadingPercent",
        attrs=width_attrs("80px"),
        orderable=False,
        viewname="report",
        args=[A("id")],
        accessor=A("loading_per"),
        empty_values=(list(), None),
    )
    # loading_usable = tables.LinkColumn(
    #     verbose_name="LoadingUsable",
    #     attrs=width_attrs("60px"),
    #     orderable=False,
    #     viewname="report",
    #     args=[A("id")],
    #     accessor=A("loading_usable"),
    #     empty_values=(list(), None),
    # )
    chip_type = tables.LinkColumn(
        verbose_name="Chip Type",
        attrs=width_attrs("60px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("chip_type"),
        empty_values=(list(), None),
    )
    TroubleShooter = tables.LinkColumn(
        verbose_name="TroubleShooter",
        attrs=width_attrs("200px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("TroubleShooter"),
        empty_values=(list(), None),
    )
    runId = tables.LinkColumn(
        verbose_name="Run Id",
        attrs=width_attrs("60px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("runId"),
        empty_values=("", None),
    )
    cf_stats = tables.LinkColumn(
        verbose_name="CF stat",
        attrs=width_attrs("160px"),
        orderable=True,
        viewname="report",
        args=[A("id")],
        accessor=A("cf_stats"),
        empty_values=("", None),
    )


    def render_time(self, value, record):
        PST = pytz.timezone("US/Pacific")
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank'>%s</a>"
            % (
                reverse("report", args=[record.id]),
                value.astimezone(PST).strftime("%Y-%b-%d %H:%M  %Z"),
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
            "time",
            "serial_number",
            "device_name",
            "archive_type",
            "runId",
            "site",
            "chip_type",
            "identifier",
            "submitter_name",
            "is_known_good",
            "TroubleShooter",
            "loading_density",
            "loading_percent",
            # "loading_usable",
            "cf_stats",
            "taser_ticket_number_txt",
            "search_tags",
        )
        # exclude the summary column data
        exclude = (
            "id",    
            "doc_file",
            "summary",
            "taser_ticket_number",
            "failure_mode",
            "sha1_hash",
            "md5_hash",
            "crc32_sum",
            "instrumentId",
        )
        show_header = True
        orderable = True
        order_by = "-date"
        empty_text = "No matches found"
        template_name = "tables/reports.html"
