from django.contrib import admin
from reports.models import (
    Archive,
    Diagnostic,
    Instrument,
)

admin.site.register(Archive)
admin.site.register(Diagnostic)
admin.site.register(Instrument)
