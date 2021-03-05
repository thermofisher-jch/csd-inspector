from django.core.management.base import BaseCommand
from reports.models import Archive
import traceback
import csv


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            nargs="?",
            default="Archive",
            help="Name of Model class to extract as CSV",
        )
        # parser.add_argument(
        #     "--manager",
        #     type=str,
        #     nargs="?",
        #     default="objects",
        #     help="Property accessor name for an optional nanager to use ",
        # )
        parser.add_argument(
            "--filter",
            type=str,
            nargs="?",
            default="",
            help="eval()'d params to filter(), otherwise all rows returned if omitted",
        )
        parser.add_argument(
            "--select",
            type=str,
            nargs="+",
            default="",
            help="Name of a model field to include in result set in same order as command argunents",
        )
        parser.add_argument(
            "--output",
            type=str,
            nargs="1",
            help="File output will be written to",
        )

    def handle(self, *args, **options):
        model = options["model"]
        manager = options["manager"]
        filter = options["filter"]
        select = options["select"]
        output = options["output"]

        if not model in SUPPORTED_MODELS:
            raise ValueError(
                "Model must be Archive (default), ValkyrieArchive or Instrument"
            )

        statement = "%s.%s" % (model, manager)
        if filter:
            statement = "%s.filter(%s)" % (filter)
        statement = "%s.value_list(%s)" % (statement, ", ".join())

        with open(output, "w") as csv_file:
            csv_writer = csv.writer(
                csv_file, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL
            )
