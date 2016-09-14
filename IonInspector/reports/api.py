from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.shortcuts import HttpResponseRedirect
from reports.models import Archive
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
import sys

class ArchiveResource(ModelResource):
    """
    Resource for archive
    """

    def prepend_urls(self):
        """
        creates new custom urls
        :return:
        """
        urls = [
            url(r"^(?P<resource_name>%s)/remove/(?P<pk>\w[\w/-]*)/$" % self._meta.resource_name, self.wrap_view('dispatch_remove'), name="api_dispatch_remove_archive"),
            url(r"^(?P<resource_name>%s)/rerun/(?P<pk>\w[\w/-]*)/$" % self._meta.resource_name, self.wrap_view('dispatch_rerun'), name="api_dispatch_rerun_archive")
        ]

        return urls

    def dispatch_remove(self, request, **kwargs):
        """
        displatch the remove request
        """
        return self.dispatch('remove', request, **kwargs)

    def dispatch_rerun(self, request, **kwargs):
        """
        displatch the rerun request
        """
        return self.dispatch('rerun', request, **kwargs)

    def post_remove(self, request, **kwargs):
        """
        The remove the archive
        """

        try:
            bundle = self.build_bundle(request=request)
            obj = self.cached_obj_get(bundle, **self.remove_api_resource_names(kwargs))
            dead_man_walking = Archive.objects.get(pk=obj.id)
            dead_man_walking.doc_file.delete(save=True)
            dead_man_walking.delete()
        except Exception as exc:
            pass

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
            return HttpResponseRedirect(reverse('reports'))


    class Meta:
        queryset = Archive.objects.all()
        resource_name = 'Archive'
        authorization = Authorization()
        remove_allowed_methods = ['post', ]
        rerun_allowed_methods = ['post', ]

