# telemetry/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .models import Project
from .serializers import PerformanceLogSerializer, ErrorLogSerializer
from .tasks import process_performance_log, process_error_log

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
