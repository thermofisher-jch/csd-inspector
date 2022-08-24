import django_tables2 as tables
from django.utils.safestring import mark_for_escaping, mark_safe
from django_tables2 import A

from reports.models import ValkyrieArchive, Archive
from .width_attrs import width_attrs


class ValkyrieInstrumentArchiveTable(tables.Table):
    """Table for rendering issue tracking report view."""

    run_number = tables.LinkColumn(
        verbose_name="Run Number",
        attrs=width_attrs("60px"),
        orderable=True,
        accessor=A("is_known_good"),
        viewname="report",
        args=[A("id")],
    )
    loading_density = tables.TemplateColumn(
        verbose_name="Loading Density",
        attrs=width_attrs("52px"),
        orderable=False,
        accessor=A("loading_density"),
        template_name="partials/loading_density_thumbnail.html",
    )
    identifier = tables.LinkColumn(
        verbose_name="Label",
        attrs=width_attrs("80px"),
        orderable=True,
        accessor=A("identifier"),
        viewname="report",
        args=[A("id")],
    )
    assay_type = tables.LinkColumn(
        verbose_name="Assay Type",
        attrs=width_attrs("128px"),
        orderable=True,
        accessor=A("assay_type"),
        viewname="report",
        args=[A("id")],
    )
    is_known_good = tables.LinkColumn(
        verbose_name="Known Good Run",
        attrs=width_attrs("64px"),
        orderable=True,
        accessor=A("is_known_good"),
        viewname="report",
        args=[A("id")],
    )
    assessment = tables.LinkColumn(
        verbose_name="Assessment",
        attrs=width_attrs("160px"),
        orderable=True,
        accessor=A("summary"),
        viewname="report",
        args=[A("id")],
    )
    failure_mode = tables.LinkColumn(
        verbose_name="Failure Mode",
        attrs=width_attrs("160px"),
        orderable=True,
        accessor=A("failure_mode"),
        viewname="report",
        args=[A("id")],
    )

    class Meta:
        model = Archive
        per_page = 10
        attrs = {"class": "table table-striped table-hover", "id": "model-table"}
        fields = (
            "run_number",
            "loading_density",
            "identifier",
            "assay_type",
            "is_known_good",
            "assessment",
            "failure_mode",
        )
        sequence = (
            "run_number",
            "loading_density",
            "identifier",
            "assay_type",
            "is_known_good",
            "assessment",
            "failure_mode",
        )
        order_by = "-run_number"
        orderable = True
        show_header = True
        template_name = "django_tables2/bootstrap.html"
        empty_text = "No matching case history found"

    def render_assay_type(self, value, record):
        return mark_safe(
            "".join(
                [
                    "<span class='label label-info'>%s</span>"
                    % mark_for_escaping(x[3:])
                    if x.startswith("<*>")
                    else "<span class='label'>%s</span>" % mark_for_escaping(x)
                    for x in value.split("; ")
                ]
            )
        )
