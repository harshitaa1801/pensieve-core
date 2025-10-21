# telemetry/views.py

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from .models import AggregatedMetric, GroupedError, Project
from .serializers import AggregatedMetricSerializer, GroupedErrorSerializer, PerformanceLogSerializer, ErrorLogSerializer
from .tasks import process_performance_log, process_error_log


class AggregatedMetricFilter(filters.FilterSet):
    """Applies a contains lookup when filtering metrics by URL."""

    url = filters.CharFilter(field_name='url', lookup_expr='icontains')

    class Meta:
        model = AggregatedMetric
        fields = ['url']

class IngestView(APIView):
    """
    A single endpoint to receive performance and error data from client libraries.
    Authenticates the project via an API key in the request header.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return Response({"error": "API key missing"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            project = Project.objects.only('id').get(api_key=api_key)
        except Project.DoesNotExist:
            return Response({"error": "Invalid API key"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        payload_type = data.get("type")
        payload = data.get("payload")

        if payload_type == "performance":
            serializer = PerformanceLogSerializer(data=payload)
            if serializer.is_valid():
                # Use Celery task to process performance log asynchronously
                process_performance_log.delay(project.id, serializer.validated_data)
                return Response(status=status.HTTP_202_ACCEPTED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif payload_type == "error":
            serializer = ErrorLogSerializer(data=payload)
            if serializer.is_valid():
                # Use Celery task to process error log asynchronously
                process_error_log.delay(project.id, serializer.validated_data)
                return Response(status=status.HTTP_202_ACCEPTED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"error": "Invalid data type specified"}, status=status.HTTP_400_BAD_REQUEST)


class GroupedErrorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only API endpoint to list the grouped errors for the
    authenticated project.
    """
    serializer_class = GroupedErrorSerializer

    def get_queryset(self):
        # Authenticate the project via the API key
        api_key = self.request.headers.get("X-API-KEY")
        if not api_key:
            return GroupedError.objects.none() # Return empty if no key

        # Filter the queryset to only show errors for this project
        return GroupedError.objects.filter(project__api_key=api_key)


class AggregatedMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only API endpoint to list aggregated performance metrics
    for the authenticated project.
    """
    serializer_class = AggregatedMetricSerializer

    RESULT_LIMIT = 100

    filter_backends = [DjangoFilterBackend] # Tell DRF to use the filter backend
    filterset_class = AggregatedMetricFilter

    def get_queryset(self):
        print(self.request.path)
        print(self.request.query_params)

        api_key = self.request.headers.get("X-API-KEY")
        if not api_key:
            return AggregatedMetric.objects.none()

        # Return metrics for this project, newest first
        return AggregatedMetric.objects.filter(
            project__api_key=api_key
        ).order_by('-timestamp')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if self.RESULT_LIMIT:
            queryset = queryset[:self.RESULT_LIMIT]

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)