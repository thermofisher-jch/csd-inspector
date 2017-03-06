from django.http import HttpRequest


def get_serialized_model(model, resource):
    """ Used to get a tastypie json object for a specific model instance. Nice for pre loading JS data structures. """
    resource_instance = resource()
    bundle = resource_instance.build_bundle(obj=model, request=HttpRequest())
    return resource_instance.serialize(None, resource_instance.full_dehydrate(bundle), 'application/json')
