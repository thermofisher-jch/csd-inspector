from django.http import HttpRequest
import os

# define constants
PGM_RUN = "PGM_Run"
PROTON = "Proton"
S5 = "S5"
OT_LOG = "OT_Log"
ION_CHEF = "Ion_Chef"
VALK = "Valkyrie"
UNKNOWN_PLATFORM = "Unknown Platform"


def get_serialized_model(model, resource):
    """ Used to get a tastypie json object for a specific model instance. Nice for pre loading JS data structures. """
    resource_instance = resource()
    bundle = resource_instance.build_bundle(obj=model, request=HttpRequest())
    return resource_instance.serialize(None, resource_instance.full_dehydrate(bundle), 'application/json')


def force_symlink(source, link):
    if os.path.exists(link):
        os.remove(link)
    os.symlink(source, link)
