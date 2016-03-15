"""
This will hold all of the data models for the inspector.
"""

from django.db import models


class Archive(models.Model):
    """
    An archive sample
    """

    # model attributes
    label = models.CharField(max_length=255)
    site = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    time = models.DateTimeField()
    status = models.CharField(max_length=255)
    submitter_name = models.CharField(max_length=255)
    archive_type = models.CharField(max_length=255)
    summary = models.CharField(max_length=255, default=u"")

    # model relationships
    # diagnostics : Foreign Key from diagnostic class
    # tags : Foreign Key from tag class


class Diagnostic(models.Model):
    """
    A test to run against an archive
    """

    # model attributes
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    priority = models.IntegerField()
    details = models.CharField(max_length=2048)
    html = models.CharField(max_length=255)

    # model relationships
    archive = models.ForeignKey(Archive, related_name="diagnostics", on_delete=models.CASCADE)


class Tag(models.Model):
    """
    A tag for an archive
    """

    # model attributes
    name = models.CharField(max_length=255)

    # model relationships
    archive = models.ForeignKey(Archive, related_name="tags")
