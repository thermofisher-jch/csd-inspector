from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils.safestring import mark_safe
import django_tables2 as tables
from django_tables2.utils import A
from reports.models import Archive
from django.core.urlresolvers import reverse


class ArchiveTable(tables.Table):
    """
    Table for rendering archives.
    """

    id = tables.Column(verbose_name='ID', attrs={'th': {'style': 'width: 60px'}}, empty_values=())
    time = tables.Column(verbose_name='Date', attrs={'th': {'style': 'width: 160px'}}, empty_values=())
    identifier = tables.Column(verbose_name='Label', orderable=True, empty_values=(), accessor='identifier',
                               attrs={'th': {'style': 'width: 30%'}})
    site = tables.Column(verbose_name='Site', attrs={'th': {'style': 'width: 20%'}}, empty_values=())
    submitter_name = tables.Column(verbose_name='Submitter', attrs={'th': {'style': 'width: 15%'}}, empty_values=())
    archive_type = tables.Column(verbose_name='Type', attrs={'th': {'style': 'width: 100px'}}, empty_values=())
    taser_ticket_number = tables.Column(verbose_name="TASER", attrs={'th': {'style': 'width: 80px'}}, empty_values=())
    search_tags = tables.Column(verbose_name="Tags", attrs={'th': {'style': 'width: 200px'}}, empty_values=())

    def render_id(self, value, record):
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank'>%s</a>" % (reverse('report', args=[record.id]), value))

    def render_time(self, value, record):
        return mark_safe("<a href='%s' class='no-underline' target='_blank'>%s</a>" % (
            reverse('report', args=[record.id]), naturaltime(value)))

    def render_identifier(self, value, record):
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank'>%s</a>" % (reverse('report', args=[record.id]), value))

    def render_site(self, value, record):
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank'>%s</a>" % (reverse('report', args=[record.id]), value))

    def render_submitter_name(self, value, record):
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank'>%s</a>" % (reverse('report', args=[record.id]), value))

    def render_archive_type(self, value, record):
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank'>%s</a>" % (reverse('report', args=[record.id]), value))

    def render_taser_ticket_number(self, value, record):
        if value:
            return mark_safe(
                "<a href='https://jira.amer.thermo.com/browse/FST-%i' target='_blank'>TASER: %i</a>" % (value, value))
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank'>&nbsp;</a>" % reverse('report', args=[record.id]))

    def render_search_tags(self, value, record):
        tags = "".join(["<span class='label'>{}</span>".format(x) for x in value])
        return mark_safe(
            "<a href='%s' class='no-underline' target='_blank' style='padding:7px'>%s</a>" % (reverse('report', args=[record.id]), tags))

    class Meta:
        model = Archive
        per_page = 100
        attrs = {
            "class": "table table-striped table-hover",
            "id": "archive_table"
        }

        # setup the column sequence
        sequence = (
            'id', 'identifier', 'taser_ticket_number', 'submitter_name', 'time', 'archive_type', 'site', 'search_tags')

        # exclude the summary column data
        exclude = ('doc_file', 'summary',)
