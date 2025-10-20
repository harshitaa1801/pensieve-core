from rest_framework import serializers
from .models import GroupedError, Project, ErrorLog, PerformanceLog


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