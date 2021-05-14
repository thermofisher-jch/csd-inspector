from django.db.models import Func
from django.http import HttpRequest
import logging
import os

from IonInspector import settings
from reports.values import DIAGNOSTICS_NAMESPACE_ROOT, GENEXUS_INSTRUMENT_TRACKER_DIAGNOSTIC_NAME, \
    DIAGNOSTICS_ROOT_ROLE

logger = logging.getLogger(__name__)


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


def _check_for_workspace_dir(dir_path, role_label):
    """Private method used to assert the existence of a workspace directory entry.  Whereas
     _ensure_workspace_dir() supports provisioning directories when a workspace is first imported
     or when its diagnostic suite is re-evaluated at bootstrap, this method exists to re-assert
     constraints expected of such directories.  It raises or reports discrepancies, but does not
     attempt to correct them itself so that task is entirely managed by code designed to be used
     for that specific funcitonal role.
     """
    if not os.path.exists(dir_path):
        raise ArchiveWorkspaceError("%s not found in bootstrapped archive workspace" % role_label)
    elif not (os.stat(dir_path).st_mode & 02775) == 02775:
        logger.warn("%s exists with incorrect permission: " % role_label)
    return dir_path


def _ensure_workspace_dir(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    elif not (os.stat(dir_path).st_mode & 02775) == 02775:
        os.chmod(dir_path, 02775)
    return dir_path


def _all_diagnostics_namespace(archive_root):
    return os.path.join(archive_root, DIAGNOSTICS_NAMESPACE_ROOT)


def find_all_diagnostics_namespace(archive_root):
    all_diagnostics_namespace = _all_diagnostics_namespace(archive_root)
    return _check_for_workspace_dir(all_diagnostics_namespace, DIAGNOSTICS_ROOT_ROLE)


def ensure_all_diagnostics_namespace(archive_root):
    all_diagnostics_namespace = _all_diagnostics_namespace(archive_root)
    return _ensure_workspace_dir(all_diagnostics_namespace)


def _diagnostic_namespace(archive_root, diagnostic_name):
    all_diagnostics_namespace = find_all_diagnostics_namespace(archive_root)
    return os.path.join(all_diagnostics_namespace, diagnostic_name)


def find_namespace_for_diagnostic(archive_root, diagnostic_name):
    diagnostic_namespace = _diagnostic_namespace(archive_root, diagnostic_name)
    return _check_for_workspace_dir(diagnostic_namespace, diagnostic_name)


def ensure_namespace_for_diagnostic(archive_root, diagnostic_name):
    all_diagnostics_namespace = _all_diagnostics_namespace(archive_root)
    _ensure_workspace_dir(all_diagnostics_namespace)
    diagnostic_namespace = _diagnostic_namespace(archive_root, diagnostic_name)
    return _ensure_workspace_dir(diagnostic_namespace)


def get_file_path(instance, filename):
    """Used for determining a path for the file to be saved to :param instance: This archive instance :param filename: The name of the file to be saved :return: The path to save the archive file to """
    media_dir = settings.MEDIA_ROOT
    if not os.path.exists(media_dir):
        os.mkdir(media_dir, 02775)
    if not (os.stat(media_dir).st_mode & 02775) == 02775:
        os.chmod(media_dir, 02775)

    archive_dirs = os.path.join(media_dir, "archive_files")
    if not os.path.exists(archive_dirs):
        os.mkdir(archive_dirs)
    if not (os.stat(archive_dirs).st_mode & 02775) == 02775:
        os.chmod(archive_dirs, 02775)

    instance_dir = os.path.join(archive_dirs, str(instance.pk))
    if not os.path.exists(instance_dir):
        os.mkdir(instance_dir, 02775)
    if not (os.stat(instance_dir).st_mode & 02775) == 02775:
        os.chmod(instance_dir, 02775)

    return os.path.join("archive_files", str(instance.pk), filename)


def is_likely_tar_file(file_path):
    return file_path.endswith(".tar") \
        or file_path.endswith(".tar.gz") \
        or file_path.endswith(".tar.xz") \
        or file_path.endswith(".txz")


class UnusableArchiveError(AssertionError):
    """ Exception class for errors preventing archive recognition """
    def __init__(self, archive_file_path, message): # real signature unknown
        super(UnusableArchiveError, self).__init__(
            str(archive_file_path) + " could not be recognized as a support archive: " + message)


class ArchiveWorkspaceError(AssertionError):
    """ Exception class for errors preventing preventing Inspector from managing its own
    local state in its archive-specific storage workspace."""
    def __init__(self,  message=""): # real signature unknown
        super(ArchiveWorkspaceError, self).__init__(message)
