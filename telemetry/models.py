from django.db import models
import uuid

class Project(models.Model):
    """A project being monitored by our APM."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    api_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}: {self.api_key}"

class ErrorLog(models.Model):
    """A single raw error event captured from a client."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="error_logs")
    timestamp = models.DateTimeField(auto_now_add=True)
    error_type = models.CharField(max_length=255)
    error_message = models.TextField()
    traceback = models.TextField()
    
    # This field is for a future feature: grouping similar errors together.
    group_hash = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

class PerformanceLog(models.Model):
    """A single raw performance data point for a request."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="performance_logs")
    timestamp = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=2048)
    method = models.CharField(max_length=10)
    status_code = models.PositiveIntegerField()
    duration_ms = models.PositiveIntegerField()

    class Meta:
        ordering = ['-timestamp']