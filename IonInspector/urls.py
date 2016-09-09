from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
# Api imports
from reports.api import ArchiveResource
from tastypie.api import Api

admin.autodiscover()

# Global site wide urls

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'reports.views.index', name='index'),
    url(r'^', include("reports.urls")),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
)

# Configure site api by importing apis from apps

v1_api = Api(api_name='v1')
v1_api.register(ArchiveResource())

archive_resource = ArchiveResource()

urlpatterns.extend(patterns(
    '',
    (r'^api/', include(v1_api.urls))
))
