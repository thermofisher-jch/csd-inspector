from django.contrib.humanize.templatetags.humanize import naturaltime
import django_tables2 as tables
from django_tables2.utils import A
from reports.models import Archive


class ArchiveTable(tables.Table):
    """
    Table for rendering archives.
    """

    id = tables.Column(verbose_name='ID')
    time = tables.Column(verbose_name='Date')
    identifier = tables.Column(verbose_name='Label')
    site = tables.Column(verbose_name='Site')
    submitter_name = tables.Column(verbose_name='Submitter')
    archive_type = tables.Column(verbose_name='Type')
    link = tables.LinkColumn('reports.views.report', args=[A('pk')], orderable=True, empty_values=(), verbose_name='Identifier', accessor='identifier')
    summary = tables.Column(verbose_name='Summary')
    taser_ticket_number = tables.Column(verbose_name="TASER")

    def render_time(self, value):
        return naturaltime(value)

    class Meta:
        model = Archive
        per_page = 100
        attrs = {
            "class": "table table-striped table-hover",
            "id": "archive_table"
        }

        # setup the column sequence
        sequence = ('id', 'taser_ticket_number', 'submitter_name', 'time', 'archive_type', 'site', 'identifier')

        # exclude the summary column data
        exclude = ('doc_file', 'link', 'summary')
