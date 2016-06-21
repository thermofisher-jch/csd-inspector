from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from IonInspector.api import ArchiveResource
from tastypie.api import Api

admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(ArchiveResource())

archive_resource = ArchiveResource()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'IonInspector.views.index', name='index'),
    url(r'^index/', 'IonInspector.views.index', name='index'),
    url(r'^upload', 'IonInspector.views.upload', name='upload'),
    url(r'^reports', 'IonInspector.views.reports', name='reports'),
    url(r'^report/(\d+)/$', 'IonInspector.views.report', name='report'),
    url(r'^diagnostic/(\w+)$', 'IonInspector.views.readme', name='readme'),
    url(r'^documentation', 'IonInspector.views.documentation', name='documentation'),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)

urlpatterns.extend(patterns(
    '',
    (r'^api/', include(v1_api.urls))
))

print urlpatterns
