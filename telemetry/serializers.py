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
        fields = ['error_type', 'count', 'last_seen', 'first_seen']


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