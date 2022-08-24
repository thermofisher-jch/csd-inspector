from django.db import models
from django.urls import reverse


class Instrument(models.Model):
    id = models.AutoField(auto_created=False, verbose_name="ID", primary_key=True)
    serial_number = models.CharField(
        verbose_name="Serial Number",
        primary_key=False,
        db_column="serial_number",
        max_length=255,
        blank=False,
        unique=True,
        null=False,
    )
    instrument_name = models.CharField(
        verbose_name="Instrument Name",
        db_column="instrument_name",
        max_length=255,
        blank=False,
        unique=False,
        null=True,
    )
    site = models.CharField(
        verbose_name="Site Name",
        db_column="site",
        max_length=255,
        blank=False,
        unique=False,
        null=True,
    )
    fas = models.CharField(
        verbose_name="Field Application Scientist",
        db_column="fas_name",
        max_length=255,
        unique=False,
        blank=True,
        null=True,
    )
    fbs = models.CharField(
        verbose_name="Field Bioinformatics Scientist",
        db_column="fbs_name",
        max_length=255,
        unique=False,
        blank=True,
        null=True,
    )
    fse = models.CharField(
        verbose_name="Field Support Engineer",
        db_column="fse_name",
        max_length=255,
        unique=False,
        blank=True,
        null=True,
    )
    # record_created_at = models.DateTimeField(
    #     name="record_created_at",
    #     verbose_name="First Created At",
    #     db_column="record_created_at",
    #     null=False,
    #     unique=False,
    # )
    # record_modified_at = models.DateTimeField(
    #     name="record_modified_at",
    #     verbose_name="Last Modified At",
    #     db_column="record_modified_at",
    #     null=False,
    #     unique=False,
    # )
    @property
    def reports_link(self):
            return "../reports/?serial_number="+self.serial_number


    class Meta:
        app_label = "reports"

    def get_absolute_url(self):
        return reverse("instrument-detail", args=[self.id])
