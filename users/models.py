from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

class User(AbstractUser):
    USER_TYPES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('delivery', 'Delivery Person'),
        ('customer', 'Customer'),
        ('inventory_manager', 'Inventory Manager'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    @property
    def is_admin(self):
        return self.user_type == 'admin'

    @property
    def is_staff_member(self):
        return self.user_type in ['admin', 'staff']

    @property
    def is_delivery_person(self):
        return self.user_type == 'delivery'

    @property
    def is_customer(self):
        return self.user_type == 'customer'

    @property
    def is_inventory_manager(self):
        return self.user_type == 'inventory_manager'


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_tokens'

    def __str__(self):
        return f"Password reset token for {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)  # Token expires in 24 hours
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired()
