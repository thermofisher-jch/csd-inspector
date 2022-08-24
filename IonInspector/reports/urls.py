from django.conf.urls import url
from django.views.generic import RedirectView

import reports.views as views

urlpatterns = [
    url(r"^index/", views.index, name="index"),
    # Nginx-assisted batch import
    url(r"^upload/batch/$", views.batch_upload, name="upload-batch"),
    # Just a CSRF token
    url(r"^csrf/$", views.CsrfView.as_view(), name="csrf"),
    # Original upload
    url(r"^upload/", views.upload, name="upload"),
    # Reports and Instruments
    url(r"^reports/", views.reports, name="reports"),
    url(r"^report/(?P<pk>\d+)/$", views.report, name="report"),
    url(r"^report/(?P<pk>\d+)/hashing/$", views.hash_archive, name="hash_archive"),
    url(
        r"^instruments/$",
        views.InstrumentsListView.as_view(),
        name="instruments-list",
    ),
    url("../reports/serial_number=(?P<serial_number>.+)$",
        views.InstrumentDetailView.as_view(),
        name="instrument-detail",
    ),
    url(r"^diagnostic/(\w+)$", views.readme, name="readme"),
    # legacy redirect
    url(
        r"^check/(?P<pk>\d+)/$",
        RedirectView.as_view(pattern_name="report", permanent=False),
    ),
]
