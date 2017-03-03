from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from reports.models import Archive
import csv
import os


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("THIS WILL DROP DATABASE TABLE!")
        if raw_input("Enter 'DROP' to continue: ") != "DROP":
            exit()
        # We cant use the ORM here. The triggers on the models attempt to mutate the file system which causes all kinds
        # of problems.
        cursor = connection.cursor()
        cursor.execute("TRUNCATE reports_tag, reports_diagnostic, reports_archive;")

        self.stdout.write("LOADING")
        input_rows = list(csv.DictReader(open(os.path.join(settings.MEDIA_ROOT, "archives.csv"))))

        largest_pk = 0

        for i, row in enumerate(input_rows):
            if i % 100 == 0:
                print "%i / %i Rows..." % (i, len(input_rows))
            # Compute archive path
            id = int(row["id"])
            path = "/var/lib/inspector/media/archive_files/%i/" % id
            archive_type = row["archive_type"]
            if archive_type in ["PGM_Run", "Proton", "Raptor_S5"]:
                path = os.path.join(path, "archive.zip")
            elif archive_type == "OT_Log":
                path = os.path.join(path, "onetouch.log")
            elif archive_type == "Ion_Chef":
                path = os.path.join(path, "logs.tar")
            else:
                raise ValueError("Unknown archive type: %s" % archive_type)

            Archive.objects.create(
                id=id,
                identifier=row["label"],
                site=row["site"],
                time=row["time"] + "-0800",
                submitter_name=row["submitter_name"],
                archive_type=archive_type,
                summary=row["summary"],
                doc_file=path
            )

            if id > largest_pk:
                largest_pk = id

        # Update the postgres seq
        largest_pk += 1
        cursor.execute("ALTER SEQUENCE reports_archive_id_seq RESTART WITH %i;" % largest_pk)

        self.stdout.write("DONE")
