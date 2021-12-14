import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.files.base import File

import pandas as pd
import traceback
import csv

import settings
from reports.models import Archive


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            nargs="?",
            default="lost_archives.csv",
            help="Location of CSV file",
        )
        parser.add_argument(
            "--offset",
            type=int,
            nargs="?",
            default=0,
            help="Number of inputs to skip over.  Begins with first record otherwise.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            nargs="?",
            default=-1,
            help="Number of inputs to process after skipping.  All rows processed if not provided.",
        )

    def handle(self, *args, **options):
        source = options["source"]
        offset = options["offset"]
        limit = options["limit"]

        # Must read all rows before skipping to parse headers
        df = pd.read_csv(
            source,
            engine="c",
            skiprows=0,
            skipinitialspace=True,
            nrows=limit + offset,
            header=0,
        )[offset:]
        present_fallback = datetime.now()

        counter = offset
        for record in df.to_records():
            try:
                file_path = os.path.join(settings.MEDIA_ROOT, record["doc_file"])
                actual_ctime = os.path.getctime(file_path)
                file_ctime = datetime.fromtimestamp(actual_ctime)
            except ValueError as ve:
                file_ctime = present_fallback

            backfill = Archive(
                id=record["id"],
                archive_type=record["archive_type"],
                identifier=record["identifier"],
                site=record["site"],
                time=file_ctime,
                submitter_name=record["submitter_name"],
                is_known_good=record["is_known_good"],
                # taser_ticket_number=record["taser_ticket_number"],
                sha1_hash=record["sha1_hash"],
                md5_hash=record["md5_hash"],
                crc32_sum=record["crc32_sum"],
            )
            backfill.doc_file.name = record["doc_file"]
            backfill.execute_diagnostics(skip_extraction=False)
            backfill.save()
            counter = counter + 1
            print("Completed " + str(counter))
        print("Complete to limit")