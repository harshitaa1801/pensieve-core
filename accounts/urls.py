from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# Create a router for API ViewSets
router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')

urlpatterns = [
    # Template-based views (web pages)
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # API endpoints for authentication
    path('api/auth/register/', views.RegisterAPIView.as_view(), name='api-register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='api-token'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('api/auth/me/', views.UserDetailAPIView.as_view(), name='api-user-detail'),
    
    # API endpoints for projects (from router)
    path('api/', include(router.urls)),
]
