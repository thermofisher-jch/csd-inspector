from django.core.management.base import BaseCommand
from reports.models import Archive
import traceback

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "pks",
            type=int,
            nargs="?",
            default=10,
            help="last number of reports to regenerate. (default: %(default)s)",
        )
        parser.add_argument(
            "-s",
            dest="start",
            default=0,
            type=int,
            help="set starting pointing. primary keys are sorted descending order.",
        )

    def handle(self, *args, **options):
        start = options["start"]
        end = options["pks"] + start
        for archive in Archive.objects.order_by("-id")[start:end]:
            try:
                archive.detect_at_create(False)
                archive.save()
                print("Archive #{}: SN{} DN{} RN {} ID{}".format(archive.id, archive.serial_number, archive.device_name, archive.runId, archive.instrumentId))
            except Exception as e:
                print("Archive #{}:".format(archive.id))
                traceback.print_exc()
