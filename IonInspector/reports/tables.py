from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils.safestring import mark_safe
import django_tables2 as tables
from django_tables2.utils import A
from reports.models import Archive


class ArchiveTable(tables.Table):
    """
    Table for rendering archives.
    """

    id = tables.Column(verbose_name='ID', attrs={'th': {'style': 'width: 60px'}})
    time = tables.Column(verbose_name='Date', attrs={'th': {'style': 'width: 150px'}})
    identifier = tables.LinkColumn('reports.views.report', args=[A('pk')], orderable=True, empty_values=(), verbose_name='Label', accessor='identifier', attrs={'th': {'style': 'width: 30%'}})
    site = tables.Column(verbose_name='Site', attrs={'th': {'style': 'width: 20%'}})
    submitter_name = tables.Column(verbose_name='Submitter', attrs={'th': {'style': 'width: 20%'}})
    archive_type = tables.Column(verbose_name='Type', attrs={'th': {'style': 'width: 100px'}})
    taser_ticket_number = tables.Column(verbose_name="TASER", attrs={'th': {'style': 'width: 80px'}})

    def render_time(self, value):
        return naturaltime(value)

    def render_taser_ticket_number(self, value):
        if value:
            return mark_safe(
                "<a href='https://jira.amer.thermo.com/browse/FST-%i' target='_blank'>TASER: %i</a>" % (value, value))
        return ""

    class Meta:
        model = Archive
        per_page = 100
        attrs = {
            "class": "table table-striped table-hover",
            "id": "archive_table"
        }

        # setup the column sequence
        sequence = ('id', 'identifier', 'taser_ticket_number', 'submitter_name', 'time', 'archive_type', 'site')

        # exclude the summary column data
        exclude = ('doc_file', 'summary', )
