from django.http import HttpRequest
from IonInspector.reports.diagnostics.common.inspector_utils import read_explog_from_handle
import zipfile
import os


def get_serialized_model(model, resource):
    """ Used to get a tastypie json object for a specific model instance. Nice for pre loading JS data structures. """
    resource_instance = resource()
    bundle = resource_instance.build_bundle(obj=model, request=HttpRequest())
    return resource_instance.serialize(None, resource_instance.full_dehydrate(bundle), 'application/json')


def force_symlink(source, link):
    if os.path.exists(link):
        os.remove(link)
    os.symlink(source, link)
