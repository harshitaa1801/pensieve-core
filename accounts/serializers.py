from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from telemetry.models import Project


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, attrs):
        """Validate password match and email uniqueness."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password."""
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model."""
    
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    api_key = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = Project
        fields = ('id', 'name', 'api_key', 'owner', 'owner_username', 'created_at')
        read_only_fields = ('id', 'api_key', 'owner', 'created_at')

    def validate_name(self, value):
        """Validate project name uniqueness for the user."""
        user = self.context['request'].user
        
        # Check if updating existing project
        if self.instance:
            # Exclude current instance from uniqueness check
            if Project.objects.filter(owner=user, name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("You already have a project with this name.")
        else:
            # Check for new project
            if Project.objects.filter(owner=user, name=value).exists():
                raise serializers.ValidationError("You already have a project with this name.")
        
        return value

    def create(self, validated_data):
        """Create a new project for the authenticated user."""
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
