# telemetry/tasks.py

import hashlib
from celery import shared_task
from .models import GroupedError, Project, PerformanceLog, ErrorLog, AggregatedMetric
from django.db import transaction
import numpy as np
from django.utils import timezone
from datetime import timedelta

@shared_task
def process_performance_log(project_id, payload):
    """Celery task to save a performance log."""
    try:
        project = Project.objects.get(id=project_id)
        PerformanceLog.objects.create(project=project, **payload)
    except Project.DoesNotExist:
        # Handle the case where the project might have been deleted
        # between the API call and the task execution.
        pass

@shared_task
def process_error_log(project_id, payload):
    """Celery task to save an error log and group it with similar errors."""
    
    def sanitize_traceback(traceback):
        """Sanitize the traceback to remove variable data like memory addresses."""
        import re
        # Example: Remove memory addresses (0x7ffdfc3b2c10)
        sanitized = re.sub(r'0x[0-9a-fA-F]+', '0xADDRESS', traceback)
        # Remove UUIDs
        sanitized_string = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '[UUID]', base_string)
        # Remove numbers (integers and floats)
        sanitized_string = re.sub(r'\b\d+\b', '[NUMBER]', sanitized_string)
        # Remove things that look like email addresses
        sanitized_string = re.sub(r'\S+@\S+', '[EMAIL]', sanitized_string)        
        return sanitized    
    
    try:
        error_type = payload.get('error_type')
        error_message = payload.get('error_message')
        traceback = payload.get('traceback')
        
        # 1. Create a base string for hashing from the parts we know are important.            
        base_string = f"{error_type}:{error_message}:{traceback}"

        # 2. Sanitize the string by removing common dynamic data patterns.
        sanitized_string = sanitize_traceback(base_string)

        # 3. Create a consistent hash from the SANITIZED string.
        hash_input = sanitized_string.encode('utf-8')
        group_hash = hashlib.sha256(hash_input).hexdigest()
    
    except Exception as e:
        # In case of any error during hashing, fallback to a simple hash.
        group_hash = hashlib.sha256(f"{payload.get('error_type')}:{payload.get('error_message')}".encode('utf-8')).hexdigest()

    try:
        project = Project.objects.get(id=project_id)

        with transaction.atomic():
            grouped_error, created = GroupedError.objects.get_or_create(
                project=project,
                group_hash=group_hash,
                url=payload.get('url'),
                defaults={'error_type': payload.get('error_type')}
            )
            if not created:
                # If the group already exists, increment the count.
                grouped_error.count += 1
                grouped_error.save()

            payload['group'] = grouped_error
            ErrorLog.objects.create(project=project, **payload)

    except Project.DoesNotExist:
        pass


@shared_task
def aggregate_performance_logs():
    """
    Aggregates raw performance logs into 5-minute windows.
    This task is scheduled to run every 5 minutes by Celery Beat.
    """
    print("Starting aggregation of performance logs...")
    # 1. Define the time window for aggregation
    end_time = timezone.now()
    start_time = end_time - timedelta(minutes=5)

    # 2. Get all logs in the last 5 minutes
    logs_to_process = PerformanceLog.objects.filter(timestamp__gte=start_time, timestamp__lt=end_time)

    # 3. Group the logs by project and URL
    logs_by_url = logs_to_process.values('project_id', 'url').distinct()

    for item in logs_by_url:
        project_id = item['project_id']
        url = item['url']

        # Get all durations for this specific project and URL
        durations = list(logs_to_process.filter(
            project_id=project_id, 
            url=url
        ).values_list('duration_ms', flat=True))

        if not durations:
            continue

        # 4. Calculate the metrics using NumPy
        request_count = len(durations)
        avg_duration = int(np.mean(durations))
        p50_duration = int(np.percentile(durations, 50)) # Median
        p95_duration = int(np.percentile(durations, 95))

        # 5. Save the aggregated data
        # We "floor" the timestamp to the start of the 5-minute window
        floored_timestamp = start_time.replace(second=0, microsecond=0)

        AggregatedMetric.objects.update_or_create(
            project_id=project_id,
            url=url,
            timestamp=floored_timestamp,
            defaults={
                'request_count': request_count,
                'avg_duration_ms': avg_duration,
                'p50_duration_ms': p50_duration,
                'p95_duration_ms': p95_duration,
            }
        )

    # We group all logs by just the project
    logs_by_project = logs_to_process.values('project_id').distinct()

    for item in logs_by_project:
        project_id = item['project_id']

        # Get all durations for this entire project in the window
        all_durations = list(logs_to_process.filter(
            project_id=project_id
        ).values_list('duration_ms', flat=True))

        if not all_durations:
            continue

        # Calculate the overall metrics
        overall_request_count = len(all_durations)
        overall_avg_duration = int(np.mean(all_durations))
        overall_p50_duration = int(np.percentile(all_durations, 50))
        overall_p95_duration = int(np.percentile(all_durations, 95))

        floored_timestamp = start_time.replace(second=0, microsecond=0)

        # Save the aggregated data with a special URL
        AggregatedMetric.objects.update_or_create(
            project_id=project_id,
            url="__overall__", # <-- Special identifier
            timestamp=floored_timestamp,
            defaults={
                'request_count': overall_request_count,
                'avg_duration_ms': overall_avg_duration,
                'p50_duration_ms': overall_p50_duration,
                'p95_duration_ms': overall_p95_duration,
            }
        )

@shared_task
def cleanup_old_raw_logs():
    """
    Deletes raw performance and error logs older than a defined retention period.
    This task is scheduled to run once a day.
    """
    # Define how long we want to keep detailed, raw logs
    retention_period = timezone.now() - timedelta(days=30) # Keep 30 days of raw logs

    # Delete old logs
    old_perf_logs = PerformanceLog.objects.filter(timestamp__lt=retention_period)
    old_error_logs = ErrorLog.objects.filter(timestamp__lt=retention_period)

    # ._raw_delete() is a faster way to delete large numbers of objects
    old_perf_logs._raw_delete(old_perf_logs.db)
    old_error_logs._raw_delete(old_error_logs.db)