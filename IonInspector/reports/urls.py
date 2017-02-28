from django.conf.urls import patterns, url
from django.views.generic import RedirectView

urlpatterns = patterns(
    '',
    url(r'^index/', 'reports.views.index', name='index'),
    url(r'^upload', 'reports.views.upload', name='upload'),
    url(r'^reports', 'reports.views.reports', name='reports'),
    url(r'^report/(?P<pk>\d+)/$', 'reports.views.report', name='report'),
    url(r'^diagnostic/(\w+)$', 'reports.views.readme', name='readme'),
    url(r'^documentation', 'reports.views.documentation', name='documentation'),

    # legacy redirect
    url(r'^check/(?P<pk>\d+)/$', RedirectView.as_view(pattern_name='report', permanent=False)),
)
