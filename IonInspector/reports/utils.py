from django.http import HttpRequest
from lemontest.diagnostics.common.inspector_utils import read_explog_from_handle
import zipfile
import os


def get_serialized_model(model, resource):
    """ Used to get a tastypie json object for a specific model instance. Nice for pre loading JS data structures. """
    resource_instance = resource()
    bundle = resource_instance.build_bundle(obj=model, request=HttpRequest())
    return resource_instance.serialize(None, resource_instance.full_dehydrate(bundle), 'application/json')


def check_for_dx_zip(path_to_zip):
    """ Checks a zip file for indicators that it's a Dx archive. Returns true if this is a Dx archive. """
    explog_data = dict()

    with zipfile.ZipFile(path_to_zip) as zip_handle:
        # make sure that the explog_final.txt exists and if not then fall back to explog.txt
        explog_filename = 'explog_final.txt' if 'explog_final.txt' in zip_handle.namelist() else 'explog.txt'

        with zip_handle.open(explog_filename) as explog_handle:
            explog_data = read_explog_from_handle(explog_handle)

    return 'Dx' in explog_data.get('SeqKitName', '')


def force_symlink(source, link):
    if os.path.exists(link):
        os.remove(link)
    os.symlink(source, link)
