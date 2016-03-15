from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings


def index(request):
    """
    Landing page request
    :param request:
    :return:
    """

    ctx = RequestContext(request, {})
    return render_to_response("index.html", context_instance=ctx)


def upload(request):
    """
    Upload an archive request
    :param request:
    :return:
    """

    ctx = RequestContext(request, {'devices': settings.TEST_MANIFEST.keys()})
    return render_to_response("upload.html", context_instance=ctx)
