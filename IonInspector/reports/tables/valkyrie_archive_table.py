import django_tables2 as tables
from django_tables2 import A

from reports.models import ValkyrieArchive
from .width_attrs import width_attrs


class ValkyrieInstrumentArchiveTable(tables.Table):
    """Table for rendering issue tracking report view."""

    # id = tables.Column(verbose_name='ID', attrs={'th': {'style': 'width: 8vw'}},
    #                      orderable=True, accessor='archive')
    run_started_at = tables.DateTimeColumn(
        verbose_name="Run Start Time",
        attrs=width_attrs("140px"),
        orderable=True,
        accessor=A("run_started_at"),
    )
    identifier = tables.LinkColumn(
        verbose_name="Label",
        attrs=width_attrs("90px"),
        orderable=True,
        accessor=A("identifier"),
        viewname="report",
        args=[A("archive_id")],
    )
    run_name = tables.LinkColumn(
        verbose_name="Run Name",
        attrs=width_attrs("300px"),
        orderable=True,
        accessor=A("run_name"),
        viewname="report",
        args=[A("archive_id")],
    )
    run_number = tables.LinkColumn(
        verbose_name="Run Number",
        attrs=width_attrs("40px"),
        orderable=True,
        accessor=A("run_number"),
        viewname="report",
        args=[A("archive_id")],
    )
    lanes_used = tables.LinkColumn(
        verbose_name="Lanes Used",
        attrs=width_attrs("75px"),
        orderable=True,
        accessor=A("lanes_used"),
        viewname="report",
        args=[A("archive_id")],
    )
    assay_types = tables.LinkColumn(
        verbose_name="Assay Types",
        attrs=width_attrs("130px"),
        orderable=True,
        accessor=A("assay_types"),
        viewname="report",
        args=[A("archive_id")],
    )
    run_type = tables.LinkColumn(
        verbose_name="Run Type",
        attrs=width_attrs("130px"),
        orderable=True,
        accessor=A("run_type"),
        viewname="report",
        args=[A("archive_id")],
    )
    is_baseline = tables.BooleanColumn(
        verbose_name="Baseline Run",
        attrs=width_attrs("30px"),
        orderable=True,
        accessor=A("is_baseline"),
    )
    assessment = tables.LinkColumn(
        verbose_name="Assessment",
        attrs=width_attrs("170px"),
        orderable=False,
        accessor=A("assessment"),
        viewname="report",
        args=[A("archive_id")],
    )
    failure_mode = tables.LinkColumn(
        verbose_name="Failure Mode",
        attrs=width_attrs("170px"),
        orderable=False,
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
            "run_name",
            "run_type",
            "lanes_used",
            "assay_types",
            "is_baseline",
            "assessment",
            "failure_mode",
        )
        sequence = (
            "run_number",
            "run_started_at",
            "identifier",
            "run_name",
            "run_type",
            "lanes_used",
            "assay_types",
            "is_baseline",
            "assessment",
            "failure_mode",
        )
        order_by = "run_started_at"
        orderable = True
        show_header = True
        template_name = "django_tables2/bootstrap.html"
        empty_text = "No case history found"
