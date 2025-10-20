from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(
        validators=[
            MinLengthValidator(10, message="Feedback message must be at least 10 characters long."),
            MaxLengthValidator(1000, message="Feedback message cannot exceed 1000 characters.")
        ],
        help_text="Please provide detailed feedback (10-1000 characters)"
    )
    rating = models.IntegerField(choices=RATING_CHOICES)
    cake_image = models.ImageField(upload_to='feedback_images/', null=True, blank=True, help_text="Upload an image of the delivered cake")
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feedback'
        ordering = ['-created_at']
    
    def clean(self):
        """Custom validation for the model"""
        super().clean()
        
        if self.message:
            # Check for repetitive characters
            if re.search(r'(.)\1{6,}', self.message):
                raise ValidationError({
                    'message': 'Please provide meaningful feedback without repetitive characters.'
                })
            
            # Check for inappropriate content
            inappropriate_words = ['spam', 'fake', 'scam', 'hate']
            if any(word in self.message.lower() for word in inappropriate_words):
                raise ValidationError({
                    'message': 'Please provide constructive feedback without inappropriate language.'
                })
            
            # For low ratings, require more detailed feedback
            if self.rating and self.rating <= 2 and len(self.message.strip()) < 20:
                raise ValidationError({
                    'message': 'For low ratings, please provide at least 20 characters explaining your experience.'
                })
    
    def save(self, *args, **kwargs):
        # Run clean validation before saving
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Feedback from {self.user.username if self.user else 'Anonymous'} - {self.rating} stars"