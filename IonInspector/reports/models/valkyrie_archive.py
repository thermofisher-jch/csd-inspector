import datetime
import os

from django.conf import settings
from django.db import models, transaction
from django.db.models import Value, Q
from django.db.models.expressions import F, When, Case
from django.db.models.functions import Concat
from django.db.models.signals import post_save
from django.dispatch import receiver

from reports.diagnostics.common.inspector_utils import read_explog
from reports.values import VALK, LANE_META_OBJECTS
from reports.utils import Concat_WS
from .instrument import Instrument
from .archive import Archive

# check to see if the settings are configured

if not settings.configured:
    settings.configure()


def lane_with_emphasis(lane_number):
    bit_mask = 1 << (lane_number - 1)
    field_name = "lane%s_assay_type" % lane_number
    emphasis_name = "lane%d_emphasis" % lane_number
    is_null_kwargs = {field_name: None}
    has_emphasis_kwargs = {emphasis_name: bit_mask}
    return Case(
        When(Q(**is_null_kwargs), Value(None)),
        When(
            Q(**has_emphasis_kwargs),
            then=Concat(Value("<*>%d(" % lane_number), F(field_name), Value(")")),
        ),
        default=Concat(Value("%d(" % lane_number), F(field_name), Value(")")),
    )


class ValkyrieArchiveQuerySet(models.QuerySet):
    def with_tracker(self):
        return self.annotate(
            serial_number=F("instrument__serial_number"),
            lane1_emphasis=F("lane_emphasis_flag").bitand(Value(1)),
            lane2_emphasis=F("lane_emphasis_flag").bitand(Value(2)),
            lane3_emphasis=F("lane_emphasis_flag").bitand(Value(4)),
            lane4_emphasis=F("lane_emphasis_flag").bitand(Value(8)),
        ).annotate(
            assay_type=Concat_WS(
                Value("; "),
                lane_with_emphasis(1),
                lane_with_emphasis(2),
                lane_with_emphasis(3),
                lane_with_emphasis(4),
            ),
        )


class ValkyrieArchiveManager(models.Manager):
    def get_queryset(self):
        return ValkyrieArchiveQuerySet(
            model=self.model,
            using=self._db,
        ).with_tracker()

    def with_tracker(self):
        return self.get_queryset().with_tracker()  # .select_related()


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
    lane_emphasis_flag = models.SmallIntegerField(
        verbose_name="Lane Emphasis Flags",
        db_column="lane_emphasis",
        db_index=False,
        editable=False,
        default=0,
        unique=False,
        blank=False,
        null=False,
    )

    class Meta:
        app_label = "reports"


# TODO: Receivers should not be imported from a model file as this can
#       lead to them registering for the same events multiple times.


@receiver(post_save, sender=Archive, dispatch_uid="update_archive")
def on_archive_update(sender, instance, **_):
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
        valkyrie_archive.is_known_good = instance.is_known_good
        valkyrie_archive.search_tags = instance.search_tags

        run_started_at = explog.get("Start Time", None)
        if not run_started_at is None:
            valkyrie_archive.run_started_at = datetime.datetime.strptime(
                run_started_at, "%m/%d/%Y %H:%M:%S"
            )
        valkyrie_archive.run_name = explog.get("runName", "Unknown")
        valkyrie_archive.run_number = int(
            valkyrie_archive.run_name[(len(device_name) + 1) :].split("-")[0]
        )
        assay_types = dict()
        emphasis_mask = 0
        for lane_meta in LANE_META_OBJECTS:
            ii = lane_meta.index
            if explog.get("LanesActive%s" % ii, "no") == "yes":
                key = "lane%s_assay_type" % ii
                lane_assay = explog.get("LanesAssay%s" % ii, None)
                if not lane_assay is None:
                    emphasis_check_file = os.path.join(
                        archive_dir, "rawTrace", "rawTrace_lane_%s.html" % ii
                    )
                    assay_types[key] = lane_assay
                    if os.path.isfile(emphasis_check_file):
                        emphasis_mask = emphasis_mask | lane_meta.bit_mask
        valkyrie_archive.lane_emphasis_flag = emphasis_mask
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
            valkyrie_archive.instrument_id = instrument_obj.id
            valkyrie_archive.save()
