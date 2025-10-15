# telemetry/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .models import Project
from .serializers import PerformanceLogSerializer, ErrorLogSerializer

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
            project = Project.objects.get(api_key=api_key)
        except Project.DoesNotExist:
            return Response({"error": "Invalid API key"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        payload_type = data.get("type")
        payload = data.get("payload")

        if payload_type == "performance":
            serializer = PerformanceLogSerializer(data=payload)
        elif payload_type == "error":
            serializer = ErrorLogSerializer(data=payload)
        else:
            return Response({"error": "Invalid data type specified"}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            # Associate the validated data with the authenticated project before saving.
            serializer.save(project=project)
            return Response(status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)