import datetime
import os
import shutil

from django.conf import settings
from django.db import models, transaction
from django.db.models import F
from django.db.models.signals import post_save, pre_delete
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
        return self.annotate(
            assessment=F("archive__summary"),
            failure_mode=F("archive__failure_mode"),
            identifier=F("archive__identifier"),
            is_baseline=F("archive__is_baseline"),
            serial_number=F("instrument__serial_number"),
        )


class ValkyrieArchiveManager(models.Manager):
    def get_queryset(self):
        return ValkyrieArchiveQuerySet(
            model=self.model,
            using=self._db,
        ).with_tracker()

    def with_tracker(self):
        return self.get_queryset().with_tracker()


class ValkyrieArchive(models.Model):
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
    run_name = models.CharField(
        verbose_name="Run Name",
        db_column="run_name",
        db_index=False,
        max_length=255,
        editable=False,
        unique=False,
        blank=False,
        null=True,
    )
    lanes_used = models.CharField(
        verbose_name="Lanes Used",
        db_column="lanes_used",
        db_index=False,
        max_length=24,
        editable=False,
        unique=False,
        blank=False,
        null=True,
    )
    run_type = models.CharField(
        verbose_name="Run Type",
        db_column="run_type",
        db_index=False,
        max_length=255,
        editable=False,
        unique=False,
        blank=False,
        null=True,
    )
    assay_types = models.CharField(
        verbose_name="Assay Types",
        db_column="assay_types",
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
        run_started_at = explog.get("Start Time", None)
        run_type = explog.get("RunType", "Unknown")
        run_name = explog.get("runName", "Unknown")

        assay_types = list()
        lanes_used = list()
        for ii in ("1", "2", "3", "4"):
            if explog.get("LanesActive%s" % ii, "no") == "yes":
                lanes_used.append(ii)
                lane_assay = explog.get("LanesAssay%s" % ii, None)
                if not lane_assay is None:
                    assay_types.append(str(lane_assay))
        lanes_used = ", ".join(lanes_used)
        assay_types = ", ".join(assay_types)
        run_number = int(run_name[(len(device_name) + 1) :].split("-")[0])

        if run_started_at is not None:
            run_started_at = datetime.datetime.strptime(
                run_started_at, "%m/%d/%Y %H:%M:%S"
            )
        valkyrie_archive = ValkyrieArchive(
            archive=instance,
            run_started_at=run_started_at,
            run_name=run_name,
            run_type=run_type,
            lanes_used=lanes_used,
            assay_types=assay_types,
            run_number=run_number,
        )
        with transaction.atomic():
            valkyrie_archive.instrument = Instrument.objects.get_or_create(
                serial_number=serial_number,
                defaults={"site": instance.site, "instrument_name": device_name},
            )[0]
            valkyrie_archive.save()
