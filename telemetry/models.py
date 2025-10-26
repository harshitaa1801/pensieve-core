from django.db import models
from django.contrib.auth.models import User
import uuid

class Project(models.Model):
    """A project being monitored by our APM."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects", null=True, blank=True)
    name = models.CharField(max_length=200)
    api_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['owner', 'name']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}: {self.api_key}"

class ErrorLog(models.Model):
    """A single raw error event captured from a client."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="error_logs")
    group = models.ForeignKey('GroupedError', on_delete=models.CASCADE, related_name="instances", null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=2048)
    method = models.CharField(max_length=10)
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


class GroupedError(models.Model):
    """Represents a group of identical errors."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="grouped_errors")
    group_hash = models.CharField(max_length=64, unique=True)
    url = models.CharField(max_length=2048)
    error_type = models.CharField(max_length=255)
    last_seen = models.DateTimeField(auto_now=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    count = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['-last_seen']

    def __str__(self):
        return f"{self.error_type} (seen {self.count} times)"


class AggregatedMetric(models.Model):
    """Stores aggregated performance metrics for a specific endpoint in a time window."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="metrics")
    url = models.CharField(max_length=2048, db_index=True)
    timestamp = models.DateTimeField(db_index=True) # The start of the aggregation window

    request_count = models.PositiveIntegerField(default=0)
    avg_duration_ms = models.PositiveIntegerField(default=0)
    p50_duration_ms = models.PositiveIntegerField(default=0) # Median
    p95_duration_ms = models.PositiveIntegerField(default=0) # 95th Percentile

    class Meta:
        ordering = ['-timestamp']
        unique_together = ['project', 'url', 'timestamp'] # Ensures one record per window

    def __str__(self):
        return f"{self.url} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"        