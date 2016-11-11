from django.conf import settings


def version_number(request):
    """Adds the version number to the contexts"""
    return {'version': settings.VERSION}
