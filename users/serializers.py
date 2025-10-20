from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, PasswordResetToken
import re

def validate_gmail_email(value):
    """Custom validator to ensure email is a Gmail address (optional for now)"""
    # For now, allow any email address
    # if not value.endswith('@gmail.com'):
    #     raise serializers.ValidationError("Email must be a Gmail address (@gmail.com)")
    return value

def validate_phone_number(value):
    """Custom validator for phone number format"""
    if value:
        # Remove all non-digit characters
        phone_digits = re.sub(r'\D', '', value)
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            raise serializers.ValidationError("Phone number must be between 10-15 digits")
    return value

class UserSerializer(serializers.ModelSerializer):
    total_orders = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'user_type', 
                 'phone_number', 'address', 'profile_picture', 'is_verified', 'is_active', 'created_at', 'date_joined', 'total_orders')
        read_only_fields = ('id', 'created_at', 'date_joined', 'total_orders')
    
    def get_total_orders(self, obj):
        """Get the total number of orders for this user"""
        return obj.orders.count()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirmPassword = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=15, required=False, validators=[validate_phone_number])
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirmPassword', 'first_name', 
                 'last_name', 'phone_number', 'address')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirmPassword']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Check if username already exists
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("Username already exists")
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already exists")
        
        # Validate email format (Gmail requirement removed for now)
        email = attrs.get('email', '')
        # if not email.endswith('@gmail.com'):
        #     raise serializers.ValidationError("Email must be a Gmail address (@gmail.com)")
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirmPassword')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # Try to authenticate with username first
            user = authenticate(username=username, password=password)
            
            # If that fails, try to authenticate with email
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')

        return attrs

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'address', 'profile_picture')


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address")


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        
        try:
            reset_token = PasswordResetToken.objects.get(token=attrs['token'])
            if not reset_token.is_valid():
                raise serializers.ValidationError("Invalid or expired reset token")
            attrs['reset_token'] = reset_token
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token")
        
        return attrs
