# telemetry/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import GroupedErrorViewSet, IngestView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'errors', GroupedErrorViewSet, basename='grouped-error')

urlpatterns = [
    path('ingest/', IngestView.as_view(), name='ingest'),

    path('', include(router.urls)),
]