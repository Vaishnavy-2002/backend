from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import User, PasswordResetToken
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer, UserProfileUpdateSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)

@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token(request):
    """Get CSRF token for API requests"""
    token = get_token(request)
    return JsonResponse({'csrfToken': token})

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def register(request):
    try:
        print(f"Registration request received: {request.data}")
        
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            print("Serializer is valid, creating user...")
            user = serializer.save()
            print(f"User created successfully: {user.username} ({user.email})")
            
            token, created = Token.objects.get_or_create(user=user)
            print(f"Token created/retrieved: {token.key}")
            
            user_data = UserSerializer(user).data
            print(f"User data serialized: {user_data}")
            
            return Response({
                'user': user_data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        else:
            print(f"Serializer validation failed: {serializer.errors}")
            return Response({
                'message': 'Registration failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    try:
        print(f"Login request received: {request.data}")
        
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            print(f"User authenticated successfully: {user.username} ({user.email})")
            
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            print(f"Token created/retrieved: {token.key}")
            
            user_data = UserSerializer(user).data
            print(f"User data serialized: {user_data}")
            
            return Response({
                'user': user_data,
                'token': token.key
            })
        else:
            print(f"Login validation failed: {serializer.errors}")
            return Response({
                'message': 'Login failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logged out successfully'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(request.user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        user_type = self.request.query_params.get('user_type', None)
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        return queryset


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users with full CRUD operations
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        user_type = self.request.query_params.get('user_type', None)
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        return queryset

    def get_permissions(self):
        """Override permissions for specific actions"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['create']:
            permission_classes = [AllowAny]  # Allow registration
        else:  # update, partial_update, destroy
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_update(self, serializer):
        """Custom update method with admin-only access"""
        user = self.request.user
        
        # Only allow admins and superusers to update users
        if not (hasattr(user, 'user_type') and (user.user_type == 'admin' or user.is_superuser)):
            raise PermissionError('Only administrators can update user accounts')
        
        # Prevent non-superusers from updating admin accounts
        instance = self.get_object()
        if instance.user_type == 'admin' and not user.is_superuser:
            raise PermissionError('You cannot update other admin accounts')
        
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """
        Delete a user - only admin users can delete other users
        """
        if not hasattr(request.user, 'user_type') or request.user.user_type != 'admin':
            return Response(
                {'message': 'Only admin users can delete other users'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        
        # Prevent admin from deleting themselves
        if instance.id == request.user.id:
            return Response(
                {'message': 'You cannot delete your own account'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent deleting other admin users unless it's a superuser
        if instance.user_type == 'admin' and not request.user.is_superuser:
            return Response(
                {'message': 'You cannot delete other admin users'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        return Response(
            {'message': f'User {instance.username} deleted successfully'}, 
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def forgot_password(request):
    """Send password reset email to user"""
    try:
        print(f"Forgot password request received: {request.data}")
        
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            print(f"Valid email: {email}")
            
            try:
                user = User.objects.get(email=email)
                print(f"User found: {user.username}")
            except User.DoesNotExist:
                return Response({
                    'message': 'No user found with this email address'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or get existing reset token
            try:
                reset_token, created = PasswordResetToken.objects.get_or_create(
                    user=user,
                    is_used=False,
                    defaults={'expires_at': None}  # Will be set in save()
                )
                print(f"Reset token created/found: {reset_token.token}")
                
                # If token already exists and is expired, create a new one
                if not created and reset_token.is_expired():
                    print("Token expired, creating new one")
                    reset_token.is_used = True
                    reset_token.save()
                    reset_token = PasswordResetToken.objects.create(user=user)
                    print(f"New reset token: {reset_token.token}")
            except Exception as e:
                print(f"Error creating reset token: {str(e)}")
                return Response({
                    'message': 'Failed to create reset token',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Generate reset URL
            reset_url = f"http://localhost:3000/reset-password?token={reset_token.token}"
            print(f"Reset URL: {reset_url}")
            
            # Send email
            subject = 'Password Reset Request - SweetBite'
            
            try:
                # Try to render the template
                print("Attempting to render email template...")
                html_message = render_to_string('emails/password_reset.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'token': reset_token.token
                })
                print("Email template rendered successfully")
                
                plain_message = strip_tags(html_message)
                print("Plain message created")
                
                # Try to send email
                print(f"Attempting to send email to: {user.email}")
                print(f"From email: {settings.DEFAULT_FROM_EMAIL}")
                
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                print("Email sent successfully!")
                
                return Response({
                    'message': 'Password reset email sent successfully'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                print(f"Email sending error: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({
                    'message': 'Failed to send email',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print(f"Serializer validation failed: {serializer.errors}")
            return Response({
                'message': 'Invalid email address',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"General error in forgot_password: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def reset_password(request):
    """Reset user password using token"""
    try:
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            reset_token = serializer.validated_data['reset_token']
            new_password = serializer.validated_data['password']
            
            # Update user password
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            return Response({
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Invalid reset data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_reset_token(request, token):
    """Verify if reset token is valid"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        if reset_token.is_valid():
            return Response({
                'valid': True,
                'email': reset_token.user.email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'valid': False,
                'message': 'Token is expired or already used'
            }, status=status.HTTP_400_BAD_REQUEST)
    except PasswordResetToken.DoesNotExist:
        return Response({
            'valid': False,
            'message': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def test_email(request):
    """Test email functionality"""
    try:
        print("Testing email functionality...")
        
        # Test template rendering
        try:
            html_message = render_to_string('emails/password_reset.html', {
                'user': {'first_name': 'Test', 'last_name': 'User', 'email': 'test@gmail.com'},
                'reset_url': 'http://localhost:3000/reset-password?token=test-token',
                'token': 'test-token'
            })
            print("✅ Template rendering successful")
        except Exception as e:
            print(f"❌ Template rendering failed: {str(e)}")
            return Response({
                'message': 'Template rendering failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Test email sending
        try:
            subject = 'Test Email - SweetBite'
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                ['test@gmail.com'],
                html_message=html_message,
                fail_silently=False,
            )
            print("✅ Email sending successful")
            
            return Response({
                'message': 'Test email sent successfully! Check Django console.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Email sending failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'message': 'Email sending failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        print(f"❌ General test error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'message': 'Test failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
