from django.contrib import admin
from reports.models import Archive, Diagnostic, Tag

admin.site.register(Archive)
admin.site.register(Diagnostic)
admin.site.register(Tag)
