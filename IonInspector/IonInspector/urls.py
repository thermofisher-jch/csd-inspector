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
    url(r'^check/(\d+)/$', 'IonInspector.views.check', name='reports')
)
