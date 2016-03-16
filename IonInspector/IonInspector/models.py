"""
This will hold all of the data models for the inspector.
"""

from django.db import models
import os


def get_file_path(instance, filename):
    """
    Used for determining a path for the file to be saved to
    :param instance:
    :param filename:
    :return:
    """
    #return os.path.join('/', 'opt', 'inspector', 'archive_files', str(instance.pk), filename)
    return os.path.join('archive_files', str(instance.pk), filename)


class Archive(models.Model):
    """
    An archive sample
    """

    # model attributes
    label = models.CharField(max_length=255)
    site = models.CharField(max_length=255)
    time = models.DateTimeField()
    submitter_name = models.CharField(max_length=255)
    archive_type = models.CharField(max_length=255)
    summary = models.CharField(max_length=255, default=u"")
    docfile = models.FileField(upload_to=get_file_path)

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
