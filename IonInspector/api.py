from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.shortcuts import HttpResponseRedirect
from IonInspector.models import Archive
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from tastypie.http import HttpAccepted


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
        bundle = self.build_bundle(request=request)
        obj = self.cached_obj_get(bundle, **self.remove_api_resource_names(kwargs))
        Archive.objects.get(pk=obj.id).delete()
        return HttpResponseRedirect(reverse('IonInspector.views.reports'))

    def post_rerun(self, request, **kwargs):
        """
        The remove the archive
        """
        bundle = self.build_bundle(request=request)
        obj = self.cached_obj_get(bundle, **self.remove_api_resource_names(kwargs))
        archive = Archive.objects.get(pk=obj.id)
        archive.execute_diagnostics()
        my_url = reverse('IonInspector.views.report', args=[archive.pk])
        return HttpResponseRedirect(my_url)

    class Meta:
        queryset = Archive.objects.all()
        resource_name = 'Archive'
        authorization = Authorization()
        remove_allowed_methods = ['post', ]
        rerun_allowed_methods = ['post', ]

