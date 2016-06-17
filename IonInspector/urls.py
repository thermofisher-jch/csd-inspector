from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

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
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT})
)
