import django_tables2 as tables
from IonInspector.models import Archive


class ArchiveTable(tables.Table):
    class Meta:
        model = Archive
        attrs = {"class": "paleblue", "width": "1000px"}
