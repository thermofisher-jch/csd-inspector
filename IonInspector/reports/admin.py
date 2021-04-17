from django.contrib import admin
from reports.models import (
    Archive,
    ValkyrieArchive,
    Diagnostic,
    Instrument,
)

admin.site.register(Archive)
admin.site.register(Diagnostic)
admin.site.register(ValkyrieArchive)
admin.site.register(Instrument)
