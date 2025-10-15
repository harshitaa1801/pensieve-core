from django.contrib import admin

from telemetry.models import Project, PerformanceLog, ErrorLog

# Register your models here.
admin.site.register(Project)
admin.site.register(PerformanceLog)
admin.site.register(ErrorLog)