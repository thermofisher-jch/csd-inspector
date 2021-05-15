import os

from django.core.management.base import BaseCommand

import settings
from reports.diagnostics.common.inspector_utils import get_filePath
from reports.models import Archive
import traceback

from reports.utils import get_file_path, ensure_all_diagnostics_namespace, \
    ensure_namespace_for_diagnostic
from reports.values import BEAD_DENSITY_FILE_NAME, GENEXUS_INSTRUMENT_TRACKER_DIAGNOSTIC_NAME


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "count",
            type=int,
            nargs="?",
            default=10,
            help="number of accounts to consider from start. (default: %(default)s)",
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
        end = options["count"] + start
        for archive_id in range(start, end):
            try:
                archive_root = os.path.join(settings.MEDIA_ROOT, "archive_files", str(archive_id))
                if not os.path.exists(archive_root):
                    continue

                print(ensure_all_diagnostics_namespace(archive_root))
                source_file_path = get_filePath(archive_root, BEAD_DENSITY_FILE_NAME)
                if source_file_path is None:
                    print("No bead density file to link for " + str(archive_id) + " in " +
                          archive_root + "\n")
                    continue

                tracker_namespace_root = ensure_namespace_for_diagnostic(
                    archive_root, GENEXUS_INSTRUMENT_TRACKER_DIAGNOSTIC_NAME)
                tracker_image_ref = os.path.join(tracker_namespace_root, BEAD_DENSITY_FILE_NAME)
                if not os.path.exists(tracker_image_ref):
                    os.symlink(source_file_path, tracker_image_ref)
                    print(source_file_path + " linked to " + tracker_image_ref + "\n")
                else:
                    print(tracker_image_ref + " is already linked\n")
            except Exception as e:
                print("Archive #{} encountered handling error:".format(archive_id))
                traceback.print_exc()
