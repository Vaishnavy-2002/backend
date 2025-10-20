from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Offer(models.Model):
    OFFER_TYPES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
        ('free_delivery', 'Free Delivery'),
        ('buy_one_get_one', 'Buy One Get One'),
        ('special', 'Special Offer'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('paused', 'Paused'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200, help_text="Offer title (e.g., 'Christmas Special')")
    description = models.TextField(help_text="Detailed offer description")
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES, default='percentage')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    
    # Offer Details
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage (0-100)"
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Fixed discount amount"
    )
    minimum_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Minimum order amount to apply offer"
    )
    
    # Validity
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    
    # Display
    banner_image = models.ImageField(
        upload_to='offers/banners/', 
        null=True, 
        blank=True,
        help_text="Banner image for the offer"
    )
    background_color = models.CharField(
        max_length=7, 
        default='#FF6B6B',
        help_text="Background color (hex code)"
    )
    text_color = models.CharField(
        max_length=7, 
        default='#FFFFFF',
        help_text="Text color (hex code)"
    )
    
    # Targeting
    is_homepage_featured = models.BooleanField(
        default=True,
        help_text="Show on homepage"
    )
    is_popup = models.BooleanField(
        default=False,
        help_text="Show as popup on homepage"
    )
    target_user_types = models.JSONField(
        default=list,
        help_text="Target specific user types (admin, customer, etc.)"
    )
    
    # Tracking
    usage_count = models.PositiveIntegerField(default=0)
    max_usage = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Maximum number of times this offer can be used"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', 
        on_delete=models.CASCADE, 
        related_name='created_offers'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        """Check if offer is currently active"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now <= self.end_date and
            (self.max_usage is None or self.usage_count < self.max_usage)
        )
    
    @property
    def is_expired(self):
        """Check if offer has expired"""
        return timezone.now() > self.end_date
    
    def can_be_used_by(self, user):
        """Check if offer can be used by specific user"""
        if not self.is_active:
            return False
        
        if self.target_user_types and user.user_type not in self.target_user_types:
            return False
        
        return True
    
    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order amount"""
        if not self.can_be_used_by(None):  # We'll pass user in actual usage
            return 0
        
        if order_amount < self.minimum_order_amount:
            return 0
        
        if self.offer_type == 'percentage' and self.discount_percentage:
            return (order_amount * self.discount_percentage) / 100
        elif self.offer_type == 'fixed' and self.discount_amount:
            return min(self.discount_amount, order_amount)
        elif self.offer_type == 'free_delivery':
            return 5.00  # Assuming delivery fee is 5.00
        
        return 0
