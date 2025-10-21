# telemetry/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AggregatedMetricViewSet, GroupedErrorViewSet, IngestView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'errors', GroupedErrorViewSet, basename='grouped-error')
router.register(r'metrics', AggregatedMetricViewSet, basename='aggregated-metric')

urlpatterns = [
    path('ingest/', IngestView.as_view(), name='ingest'),

    path('pensieve/', include(router.urls)),
]