import django_tables2 as tables
from django_tables2.utils import A
from reports.models import Archive


class ArchiveTable(tables.Table):
    """
    Table for rendering archives.
    """

    time = tables.Column(verbose_name='Upload Time')
    identifier = tables.Column(verbose_name='Identifier')
    site = tables.Column(verbose_name='Site')
    submitter_name = tables.Column(verbose_name='Submitter Name')
    archive_type = tables.Column(verbose_name='Type')
    link = tables.LinkColumn('reports.views.report', args=[A('pk')], orderable=True, empty_values=(),
                             verbose_name='Identifier', accessor='identifier')

    class Meta:
        model = Archive
        per_page = 25
        attrs = {
            "class": "paleblue",
            "id": "archive_table"
        }

        # setup the column sequence
        sequence = ('time', 'site', 'submitter_name', 'archive_type', 'link')

        # exclude the summary column data
        exclude = ('summary', 'doc_file', 'id', 'identifier')

