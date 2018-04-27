from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.shortcuts import HttpResponseRedirect, HttpResponse
from reports.models import Archive, Diagnostic
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from tastypie.fields import CharField, ToManyField
import json
import logging

logger = logging.getLogger(__name__)


class DiagnosticResource(ModelResource):
    readme = CharField(readonly=True)

    def dehydrate_readme(self, bundle):
        return bundle.obj.readme

    class Meta:
        queryset = Diagnostic.objects.all()
        resource_name = 'Diagnostic'
        authorization = Authorization()


class ArchiveResource(ModelResource):
    """
    Resource for archive
    """
    diagnostics = ToManyField(DiagnosticResource, 'diagnostics', full=True, use_in="detail")

    def prepend_urls(self):
        """
        creates new custom urls
        :return:
        """
        urls = [
            url(r"^(?P<resource_name>%s)/remove/(?P<pk>\w[\w/-]*)/$" % self._meta.resource_name, self.wrap_view('dispatch_remove'), name="api_dispatch_remove_archive"),
            url(r"^(?P<resource_name>%s)/rerun/(?P<pk>\w[\w/-]*)/$" % self._meta.resource_name, self.wrap_view('dispatch_rerun'), name="api_dispatch_rerun_archive"),
            url(r"^(?P<resource_name>%s)/values/$" % self._meta.resource_name, self.wrap_view('dispatch_values'), name="api_dispatch_values_archive")
        ]

        return urls

    def dispatch_remove(self, request, **kwargs):
        """
        dispatch the remove request
        """
        return self.dispatch('remove', request, **kwargs)

    def dispatch_rerun(self, request, **kwargs):
        """
        dispatch the rerun request
        """
        return self.dispatch('rerun', request, **kwargs)

    def dispatch_values(self, request, **kwargs):
        """
        dispatch the values request
        """
        return self.dispatch('values', request, **kwargs)

    def post_remove(self, request, **kwargs):
        """
        The remove the archive
        """

        bundle = self.build_bundle(request=request)
        obj = self.cached_obj_get(bundle, **self.remove_api_resource_names(kwargs))
        dead_man_walking = Archive.objects.get(pk=obj.id)
        dead_man_walking.delete()

        return HttpResponseRedirect(reverse('reports'))

    def post_rerun(self, request, **kwargs):
        """
        The remove the archive
        """

        try:
            bundle = self.build_bundle(request=request)
            obj = self.cached_obj_get(bundle, **self.remove_api_resource_names(kwargs))
            archive = Archive.objects.get(pk=obj.id)
            archive.execute_diagnostics()
            my_url = reverse('report', kwargs={'pk': obj.id})
            return HttpResponseRedirect(my_url)
        except Exception as exc:
            logger.exception(exc)
            return HttpResponseRedirect(reverse('reports'))

    def get_values(self, request, **kwargs):
        """
        Returns a values list for a specific field. Returns values that start with 'q' and ordered by the usage count.
        """
        field = request.GET.get("field", None)
        query = request.GET.get("q", None)
        response = {
            "values": []
        }
        if field and query:
            kwargs = {
                "%s__istartswith" % field: query
            }
            values_dict = list(Archive.objects.filter(**kwargs)
                               .values(field)
                               .order_by(field)
                               .annotate(usage_count=Count(field))
                               .order_by("-usage_count"))
            response["values"] = [value_dict[field] for value_dict in values_dict]
        return HttpResponse(json.dumps(response), content_type="application/json")

    def dehydrate_doc_file(self, bundle):
        # Work around for this bug: https://groups.google.com/forum/#!topic/django-tastypie/cxrI6Cl1z4s
        # need dehydrate to return the path instead of the url
        # patch first gets the dehydrated model and then modifies it
        # which breaks when the file field gets turned from a path into a url
        return bundle.obj.doc_file

    doc_file_url = CharField(readonly=True)

    def dehydrate_doc_file_url(self, bundle):
        # The api consumer probably wants the url instead of the file path
        if bundle.obj.doc_file:
            return bundle.obj.doc_file.url
        else:
            return None

    class Meta:
        queryset = Archive.objects.all()
        resource_name = 'Archive'
        authorization = Authorization()
        remove_allowed_methods = ['post', ]
        rerun_allowed_methods = ['post', ]
        values_allowed_methods = ['get', ]
        ordering = ['id', ]