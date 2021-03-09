import datetime
import os

from django.conf import settings
from django.db import models, transaction
from django.db.models import Case, When, Value, ExpressionWrapper, CharField
from django.db.models.expressions import F
from django.db.models.functions import Concat
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from reports.diagnostics.common.inspector_utils import read_explog
from .instrument import Instrument
from .archive import Archive
from reports.values import VALK

# check to see if the settings are configured
if not settings.configured:
    settings.configure()


class ValkyrieArchiveQuerySet(models.QuerySet):
    def with_tracker(self):
        qs_with_exprs = self.annotate(
            serial_number=F("instrument__serial_number"),
            lane1_comma=(
                ExpressionWrapper(
                    Concat(Value("1("), F("lane1_assay_type"), Value("), ")),
                    output_field=CharField(),
                )
            ),
            lane2_comma=(
                ExpressionWrapper(
                    Concat(Value("2("), F("lane2_assay_type"), Value("), ")),
                    output_field=CharField(),
                )
            ),
            lane3_comma=(
                ExpressionWrapper(
                    Concat(Value("3("), F("lane3_assay_type"), Value("), ")),
                    output_field=CharField(),
                )
            ),
            lane4_comma=(
                ExpressionWrapper(
                    Concat(Value("4("), F("lane4_assay_type"), Value("), ")),
                    output_field=CharField(),
                )
            ),
        )
        return qs_with_exprs.annotate(
            assay_type=Case(
                When(
                    lane4_assay_type__isnull=Value(False),
                    then=Concat(
                        F("lane1_comma"),
                        Concat(
                            F("lane2_comma"),
                            Concat(
                                F("lane3_comma"),
                                Value("4("),
                                F("lane4_assay_type"),
                                Value(")"),
                            ),
                        ),
                    ),
                ),
                When(
                    lane3_assay_type__isnull=Value(False),
                    then=Concat(
                        F("lane1_comma"),
                        Concat(
                            F("lane2_comma"),
                            Value("3("),
                            F("lane3_assay_type"),
                            Value(")"),
                        ),
                    ),
                ),
                When(
                    lane2_assay_type__isnull=Value(False),
                    then=Concat(
                        F("lane1_comma"),
                        Value("2("),
                        F("lane2_assay_type"),
                        Value(")"),
                    ),
                ),
                default=Concat(Value("1("), F("lane1_assay_type"), Value(")")),
                output_field=CharField(),
            ),
        )


class ValkyrieArchiveManager(models.Manager):
    def get_queryset(self):
        return ValkyrieArchiveQuerySet(
            model=self.model,
            using=self._db,
        ).with_tracker()

    def with_tracker(self):
        return self.get_queryset().with_tracker().select_related()


class ValkyrieArchive(Archive):
    objects = ValkyrieArchiveManager()

    archive = models.OneToOneField(
        "Archive",
        verbose_name="Archive ID",
        db_column="id",
        related_name="as_valkyrie",
        parent_link=True,
        primary_key=True,
    )
    instrument = models.ForeignKey(
        "Instrument",
        verbose_name="Host Instrument",
        db_column="instrument",
        related_name="valkyrie_archives",
        on_delete=models.PROTECT,
        db_index=True,
        unique=False,
        null=True,
    )
    run_number = models.SmallIntegerField(
        verbose_name="Run Number",
        db_column="run_number",
        db_index=False,
        unique=False,
        null=False,
    )
    # Customer started experiment run at
    run_started_at = models.DateTimeField(
        verbose_name="Run Start Time",
        db_column="run_started_at",
        db_index=True,
        unique=False,
        null=False,
    )
    lane1_assay_type = models.CharField(
        verbose_name="Lane1 Assay Type",
        db_column="lane1_assay",
        db_index=False,
        max_length=255,
        editable=False,
        unique=False,
        blank=False,
        null=True,
    )
    lane2_assay_type = models.CharField(
        verbose_name="Lane2 Assay Type",
        db_column="lane2_assay",
        db_index=False,
        max_length=255,
        editable=False,
        unique=False,
        blank=False,
        null=True,
    )
    lane3_assay_type = models.CharField(
        verbose_name="Lane3 Assay Type",
        db_column="lane3_assay",
        db_index=False,
        max_length=255,
        editable=False,
        unique=False,
        blank=False,
        null=True,
    )
    lane4_assay_type = models.CharField(
        verbose_name="Lane4 Assay Type",
        db_column="lane4_assay",
        db_index=False,
        max_length=255,
        editable=False,
        unique=False,
        blank=False,
        null=True,
    )

    class Meta:
        app_label = "reports"

    def get_absolute_url(self):
        return reverse("report", args=[self.archive_id])


# TODO: Receivers should not be imported from a model file as this can
#       lead to them registering for the same events multiple times.


@receiver(post_save, sender=Archive, dispatch_uid="update_archive")
def on_archive_update(sender, instance, **kwargs):
    if instance.archive_type == VALK:
        archive_dir = os.path.dirname(instance.doc_file.path)
        explog = read_explog(archive_dir)
        serial_number = explog.get("Serial Number", None)
        device_name = explog.get("DeviceName", None)

        try:
            valkyrie_archive = instance.as_valkyrie
        except AttributeError:  # RelatedObjectDoesNotExist:
            valkyrie_archive = ValkyrieArchive(archive=instance)

        if valkyrie_archive.instrument is not None:
            # No need to initialize this a second or subsequent time.
            return

        valkyrie_archive.archive_id = instance.id
        valkyrie_archive.archive_type = instance.archive_type
        valkyrie_archive.identifier = instance.identifier
        valkyrie_archive.doc_file = instance.doc_file
        valkyrie_archive.failure_mode = instance.failure_mode
        valkyrie_archive.summary = instance.summary
        valkyrie_archive.site = instance.site
        valkyrie_archive.submitter_name = instance.submitter_name
        valkyrie_archive.taser_ticket_number = instance.taser_ticket_number
        valkyrie_archive.time = instance.time
        valkyrie_archive.search_tags = instance.search_tags

        run_started_at = explog.get("Start Time", None)
        valkyrie_archive.run_name = explog.get("runName", "Unknown")
        valkyrie_archive.run_number = int(
            valkyrie_archive.run_name[(len(device_name) + 1) :].split("-")[0]
        )
        assay_types = dict()
        for ii in ("1", "2", "3", "4"):
            if explog.get("LanesActive%s" % ii, "no") == "yes":
                key = "lane%s_assay_type" % ii
                lane_assay = explog.get("LanesAssay%s" % ii, None)
                if not lane_assay is None:
                    emphasis_check_file = os.path.join(
                        archive_dir, "rawTrace", "rawTrace_lane_%s.html" % ii
                    )
                    if os.path.isfile(emphasis_check_file):
                        assay_types[key] = "<b>%s</b>" % str(lane_assay)
                    else:
                        assay_types[key] = str(lane_assay)

        valkyrie_archive.run_started_at = datetime.datetime.strptime(
            run_started_at, "%m/%d/%Y %H:%M:%S"
        )
        if "lane1_assay_type" in assay_types:
            valkyrie_archive.lane1_assay_type = assay_types["lane1_assay_type"]
        if "lane2_assay_type" in assay_types:
            valkyrie_archive.lane2_assay_type = assay_types["lane2_assay_type"]
        if "lane3_assay_type" in assay_types:
            valkyrie_archive.lane3_assay_type = assay_types["lane3_assay_type"]
        if "lane4_assay_type" in assay_types:
            valkyrie_archive.lane4_assay_type = assay_types["lane4_assay_type"]

        with transaction.atomic():
            instrument_result = Instrument.objects.get_or_create(
                serial_number=serial_number,
                defaults={
                    "site": valkyrie_archive.site,
                    "instrument_name": device_name,
                },
            )
            if instrument_result[1]:
                print("Created a new object")
            else:
                print("Reusing a previously created dependency")
            instrument_obj = instrument_result[0]
            print("Today I met a " + str(instrument_obj))
            valkyrie_archive.instrument_id = instrument_obj.id
            valkyrie_archive.save()
