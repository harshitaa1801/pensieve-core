from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

from .serializers import RegisterSerializer, UserSerializer, ProjectSerializer
from telemetry.models import Project


# ============ Template-based Views (for web pages) ============

def home_view(request):
    """Landing page view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def signup_view(request):
    """User registration page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Validation
        if not username or not email or not password:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'accounts/signup.html')
        
        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'accounts/signup.html')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'accounts/signup.html')
    
    return render(request, 'accounts/signup.html')


def login_view(request):
    """User login page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'accounts/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'accounts/login.html')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """User logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard_view(request):
    """Dashboard showing user's projects."""
    projects = Project.objects.filter(owner=request.user).order_by('-created_at')
    
    # Handle project creation
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            project_name = request.POST.get('project_name')
            
            if not project_name:
                messages.error(request, 'Project name is required.')
            elif Project.objects.filter(owner=request.user, name=project_name).exists():
                messages.error(request, 'You already have a project with this name.')
            else:
                try:
                    project = Project.objects.create(
                        owner=request.user,
                        name=project_name
                    )
                    messages.success(request, f'Project "{project_name}" created successfully!')
                    return redirect('dashboard')
                except Exception as e:
                    messages.error(request, f'Error creating project: {str(e)}')
        
        elif action == 'delete':
            project_id = request.POST.get('project_id')
            try:
                project = Project.objects.get(id=project_id, owner=request.user)
                project_name = project.name
                project.delete()
                messages.success(request, f'Project "{project_name}" deleted successfully.')
                return redirect('dashboard')
            except Project.DoesNotExist:
                messages.error(request, 'Project not found.')
            except Exception as e:
                messages.error(request, f'Error deleting project: {str(e)}')
        
        elif action == 'regenerate':
            project_id = request.POST.get('project_id')
            try:
                project = Project.objects.get(id=project_id, owner=request.user)
                import uuid
                project.api_key = uuid.uuid4()
                project.save()
                messages.success(request, f'API key regenerated for project "{project.name}".')
                return redirect('dashboard')
            except Project.DoesNotExist:
                messages.error(request, 'Project not found.')
            except Exception as e:
                messages.error(request, f'Error regenerating API key: {str(e)}')
    
    context = {
        'projects': projects,
        'user': request.user
    }
    return render(request, 'accounts/dashboard.html', context)


# ============ REST API Views (for API endpoints) ============

class RegisterAPIView(generics.CreateAPIView):
    """API endpoint for user registration."""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class UserDetailAPIView(generics.RetrieveUpdateAPIView):
    """API endpoint to get and update current user details."""
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ProjectViewSet(viewsets.ModelViewSet):
    """API endpoints for project CRUD operations."""
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return only projects owned by the authenticated user."""
        return Project.objects.filter(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def regenerate_key(self, request, pk=None):
        """Regenerate API key for a project."""
        import uuid
        project = self.get_object()
        project.api_key = uuid.uuid4()
        project.save()
        
        serializer = self.get_serializer(project)
        return Response({
            'message': 'API key regenerated successfully',
            'project': serializer.data
        })
