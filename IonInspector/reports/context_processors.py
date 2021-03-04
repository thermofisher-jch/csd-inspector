from django.conf import settings


def version_number(request):
    """Adds the version number to the contexts"""
    return {"version": settings.VERSION}


def active_nav(request):
    """Adds the active nav to the contexts"""
    active_urls = {
        "index": "INDEX",
        "upload": "SUBMIT",
        "reports": "REPORT",
        "report": "REPORT",
        "instrument-detail": "INSTRUMENT",
        "instruments-list": "INSTRUMENT",
        "readme": "REPORT",
        "documentation": "DOCS",
    }
    return {"active_nav": active_urls.get(request.resolver_match.url_name)}
