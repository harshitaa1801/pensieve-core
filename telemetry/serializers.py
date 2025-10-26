from rest_framework import serializers
from .models import AggregatedMetric, GroupedError, Project, ErrorLog, PerformanceLog


class ErrorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorLog
        fields = ['error_type', 'error_message', 'traceback', 'url', 'method']


class PerformanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceLog
        fields = ['url', 'method', 'status_code', 'duration_ms']


class GroupedErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupedError
        fields = ['group_hash', 'error_type', 'count', 'last_seen', 'first_seen']


class AggregatedMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = AggregatedMetric
        fields = [
            'url', 
            'timestamp', 
            'request_count', 
            'avg_duration_ms', 
            'p50_duration_ms', 
            'p95_duration_ms'
        ]


class ErrorLogInstanceSerializer(serializers.ModelSerializer):
    """Serializes a single, raw error log instance."""
    class Meta:
        model = ErrorLog
        fields = ['timestamp', 'error_message', 'traceback']

class GroupedErrorDetailSerializer(serializers.ModelSerializer):
    """Serializes a grouped error plus its latest instance."""
    latest_instance = serializers.SerializerMethodField()

    class Meta:
        model = GroupedError
        fields = [
            'error_type', 
            'count', 
            'last_seen', 
            'first_seen', 
            'latest_instance'
        ]
    
    def get_latest_instance(self, obj):
        # Get the most recent raw log for this group
        latest = obj.instances.order_by('-timestamp').first()
        if latest:
            return ErrorLogInstanceSerializer(latest).data
        return None