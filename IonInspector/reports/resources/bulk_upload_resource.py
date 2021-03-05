import logging
from django.http import HttpResponse
from django.views import View
from tastypie.http import HttpAccepted, HttpNoContent


logger = logging.getLogger(__name__)


class BulkUploadResource(View):
    class Meta:
        allowed_methods = ["post", "get"]

    def __init__(self, **kwargs):
        super(BulkUploadResource, self).__init__(**kwargs)
        self.get_count = 0

    def post(self, request, **_):
        return HttpAccepted()

    def get(self, request, **_):
        self.get_count = self.get_count + 1
        if self.get_count == 5:
            self.get_count = 0
            logger.error("No content every 5th")
            return HttpNoContent()
        logger.error("Content already received")
        return HttpResponse()

    # def put_list(self, request, **kwargs):
    #     print(request.body)

    # def put_detail(self, request, **kwargs):
    #     print(request.body)
