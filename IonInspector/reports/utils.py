from django.db.models import Func
from django.http import HttpRequest
import os

from IonInspector import settings


class Unnest(Func):
    """Function node for unroling Postgres's Array data type from a row of one list to N rows of single values"""
    function = "UNNEST"


class Concat_WS(Func):
    """Function node PostgresQL's ConcatW() function for concatenating colimns with a delimiter"""

    function = "CONCAT_WS"


def get_serialized_model(model, resource):
    """Used to get a tastypie json object for a specific model instance.
    Nice for pre loading JS data structures."""
    resource_instance = resource()
    bundle = resource_instance.build_bundle(obj=model, request=HttpRequest())
    return resource_instance.serialize(
        None, resource_instance.full_dehydrate(bundle), "application/json"
    )


def force_symlink(source, link):
    if os.path.exists(link):
        os.remove(link)
    os.symlink(source, link)


def get_file_path(instance, filename):
    """Used for determining a path for the file to be saved to :param instance: This archive instance :param filename: The name of the file to be saved :return: The path to save the archive file to """
    media_dir = settings.MEDIA_ROOT
    if not os.path.exists(media_dir):
        os.mkdir(media_dir, 0777)
    if not (os.stat(media_dir).st_mode & 0777) == 0777:
        os.chmod(media_dir, 0777)

    archive_dirs = os.path.join(media_dir, "archive_files")
    if not os.path.exists(archive_dirs):
        os.mkdir(archive_dirs)
    if not (os.stat(archive_dirs).st_mode & 0777) == 0777:
        os.chmod(archive_dirs, 0777)

    instance_dir = os.path.join(archive_dirs, str(instance.pk))
    if not os.path.exists(instance_dir):
        os.mkdir(instance_dir, 0777)
    if not (os.stat(instance_dir).st_mode & 0777) == 0777:
        os.chmod(instance_dir, 0777)

    return os.path.join("archive_files", str(instance.pk), filename)
