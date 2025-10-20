from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_active', 'is_verified', 'created_at')
    list_filter = ('user_type', 'is_active', 'is_verified', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('SweetBite Info', {
            'fields': ('user_type', 'phone_number', 'address', 'profile_picture', 'is_verified')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('SweetBite Info', {
            'fields': ('user_type', 'phone_number', 'address', 'profile_picture', 'is_verified')
        }),
    )
