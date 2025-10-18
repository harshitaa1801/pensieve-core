from django.contrib import admin

from telemetry.models import GroupedError, Project, PerformanceLog, ErrorLog

# Register your models here.
admin.site.register(Project)
admin.site.register(PerformanceLog)
admin.site.register(ErrorLog)
admin.site.register(GroupedError)