from django.conf.urls import url
from django.views.generic import RedirectView

import reports.views as views

urlpatterns = [
    url(r"^index/", views.index, name="index"),
    url(r"^upload/", views.upload, name="upload"),
    url(r"^reports/", views.reports, name="reports"),
    url(r"^report/(?P<pk>\d+)/$", views.report, name="report"),
    url(r"^diagnostic/(\w+)$", views.readme, name="readme"),
    # legacy redirect
    url(
        r"^check/(?P<pk>\d+)/$",
        RedirectView.as_view(pattern_name="report", permanent=False),
    ),
]
