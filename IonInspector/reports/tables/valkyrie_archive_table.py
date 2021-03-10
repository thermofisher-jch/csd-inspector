import django_tables2 as tables
from django_tables2 import A

from reports.models import ValkyrieArchive, Archive
from .width_attrs import width_attrs


class ValkyrieInstrumentArchiveTable(tables.Table):
    """Table for rendering issue tracking report view."""

    run_number = tables.LinkColumn(
        verbose_name="Run Number",
        attrs=width_attrs("64px"),
        orderable=True,
        accessor=A("run_number"),
        viewname="report",
        args=[A("archive_id")],
    )
    run_started_at = tables.DateColumn(
        verbose_name="Run Start Date",
        attrs=width_attrs("72px"),
        short=True,
        orderable=True,
        accessor=A("run_started_at"),
    )
    identifier = tables.LinkColumn(
        verbose_name="Label",
        attrs=width_attrs("100px"),
        orderable=True,
        accessor=A("identifier"),
        viewname="report",
        args=[A("archive_id")],
    )
    assay_type = tables.LinkColumn(
        verbose_name="Assay Type",
        attrs=width_attrs("140px"),
        orderable=True,
        accessor=A("assay_type"),
        viewname="report",
        args=[A("archive_id")],
    )
    is_known_good = tables.LinkColumn(
        verbose_name="Known Good Run",
        attrs=width_attrs("64px"),
        orderable=True,
        accessor=A("is_known_good"),
        viewname="report",
        args=[A("archive_id")],
    )
    assessment = tables.LinkColumn(
        verbose_name="Assessment",
        attrs=width_attrs("164px"),
        orderable=True,
        accessor=A("assessment"),
        viewname="report",
        args=[A("archive_id")],
    )
    failure_mode = tables.LinkColumn(
        verbose_name="Failure Mode",
        attrs=width_attrs("164px"),
        orderable=True,
        accessor=A("failure_mode"),
        viewname="report",
        args=[A("archive_id")],
    )

    class Meta:
        model = ValkyrieArchive
        per_page = 10
        attrs = {"class": "table table-striped table-hover", "id": "model-table"}
        fields = (
            "run_number",
            "run_started_at",
            "identifier",
            "assay_type",
            "is_known_good",
            "assessment",
            "failure_mode",
        )
        sequence = (
            "run_number",
            "run_started_at",
            "identifier",
            "assay_type",
            "is_known_good",
            "assessment",
            "failure_mode",
        )
        order_by = "-run_started_at"
        orderable = True
        show_header = True
        template_name = "django_tables2/bootstrap.html"
        empty_text = "No matching case history found"
