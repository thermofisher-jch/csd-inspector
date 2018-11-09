from django.core.management.base import BaseCommand
from reports.models import Archive
import traceback


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('pks', type=int)

    def handle(self, *args, **options):
        for archive in Archive.objects.order_by("-id")[:options['pks']]:
            try:
                archive.generate_tags()
            except Exception as e:
                print("Archive #{}:".format(archive.id))
                traceback.print_exc()
