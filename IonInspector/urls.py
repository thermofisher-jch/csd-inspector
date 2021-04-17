from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import RedirectView
from tastypie.api import Api

from IonInspector.custom_static_serve import custom_serve
from reports.api import ArchiveResource
from reports.views import index

admin.autodiscover()

# Global site wide urls
urlpatterns = [
    url(r"^admin/", include(admin.site.urls)),
    url(r"^$", index, name="index"),
    url(r"^", include("IonInspector.reports.urls")),
    url(
        r"^media/(?P<path>.*)$",
        custom_serve,
        {"document_root": settings.MEDIA_ROOT, "show_indexes": True},
    ),
    # in order to support coverage analysis html output files we need to replicate the Torrent suite static file serving
    url(
        r"^site_media/resources/bootstrap/css/bootstrap.min.css$",
        RedirectView.as_view(url="/static/css/bootstrap.css", permanent=True),
    ),
    url(
        r"^site_media/resources/kendo/styles/kendo.common.min.css$",
        RedirectView.as_view(url="/static/css/kendo.common.min.css", permanent=True),
    ),
    url(
        r"^site_media/resources/less/kendo.tb.min.css$",
        RedirectView.as_view(url="/static/css/kendo.tb.css", permanent=True),
    ),
    url(
        r"^site_media/resources/styles/tb-layout.css$",
        RedirectView.as_view(url="/static/css/tb-layout.min.css", permanent=True),
    ),
    url(
        r"^site_media/resources/styles/tb-styles.min.css$",
        RedirectView.as_view(url="/static/css/tb-styles.min.css", permanent=True),
    ),
    url(
        r"^site_media/stylesheet.css$",
        RedirectView.as_view(url="/static/css/stylesheet.css", permanent=True),
    ),
    url(
        r"^site_media/resources/styles/print.css$",
        RedirectView.as_view(url="/static/css/print.css", permanent=True),
    ),
    url(
        r"^site_media/resources/styles/report.css$",
        RedirectView.as_view(url="/static/css/report.css", permanent=True),
    ),
    url(
        r"^site_media/resources/jquery/jquery-1.8.2.min.js$",
        RedirectView.as_view(url="/static/js/jquery-1.8.3.min.js", permanent=True),
    ),
    url(
        r"^site_media/resources/scripts/kendo.custom.min.js$",
        RedirectView.as_view(url="/static/js/kendo.custom.min.js", permanent=True),
    ),
]

urlpatterns += staticfiles_urlpatterns()

# Configure site api by importing apis from apps

v1_api = Api(api_name="v1")
v1_api.register(ArchiveResource())

archive_resource = ArchiveResource()

urlpatterns.extend([url(r"^api/", include(v1_api.urls))])
