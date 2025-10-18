# telemetry/tasks.py

import hashlib
from celery import shared_task
from .models import GroupedError, Project, PerformanceLog, ErrorLog
from django.db import transaction

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