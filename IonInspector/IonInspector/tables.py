import django_tables2 as tables
from django_tables2.utils import A
from IonInspector.models import Archive


class ArchiveTable(tables.Table):
    """
    Table for rendering archives.
    """

    link = tables.LinkColumn('report', args=[A('pk')], orderable=False, empty_values=(), verbose_name='Report Details', accessor='pk')

    class Meta:
        model = Archive
        attrs = {
            "class": "paleblue",
            "width": "1000px"
        }

        # setup the column sequence
        sequence = ('time', 'label', 'site', 'submitter_name', 'archive_type', 'link')

        # exclude the summary column data
        exclude = ('summary', 'doc_file', 'id')

