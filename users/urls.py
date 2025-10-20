from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSet
router = DefaultRouter()
router.register(r'users', views.UserViewSet)

app_name = 'users'

urlpatterns = [
    path('csrf/', views.csrf_token, name='csrf_token'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/forgot-password/', views.forgot_password, name='forgot_password'),
    path('auth/reset-password/', views.reset_password, name='reset_password'),
    path('auth/verify-reset-token/<uuid:token>/', views.verify_reset_token, name='verify_reset_token'),
    path('auth/test-email/', views.test_email, name='test_email'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    # Include router URLs for full CRUD operations
    path('', include(router.urls)),
    # Keep the old users/ endpoint for backward compatibility
    path('users/', views.UserListAPIView.as_view(), name='user_list'),
]
