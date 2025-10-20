from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date


class SeasonalEvent(models.Model):
    """Model to store seasonal events and their sales data"""
    
    SALES_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('peak', 'Peak'),
    ]
    
    ICON_CHOICES = [
        ('heart', 'Heart'),
        ('gift', 'Gift'),
        ('sparkles', 'Sparkles'),
        ('fire', 'Fire'),
        ('star', 'Star'),
        ('calendar', 'Calendar'),
    ]
    
    COLOR_CHOICES = [
        ('red', 'Red'),
        ('orange', 'Orange'),
        ('yellow', 'Yellow'),
        ('green', 'Green'),
        ('blue', 'Blue'),
        ('purple', 'Purple'),
        ('pink', 'Pink'),
    ]
    
    name = models.CharField(max_length=100, help_text="Event name (e.g., Valentine's Day)")
    description = models.TextField(blank=True, help_text="Event description")
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month (1-12)"
    )
    day = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of month (1-31)"
    )
    year = models.IntegerField(
        default=2025,
        help_text="Year (defaults to current year)"
    )
    sales_level = models.CharField(
        max_length=10,
        choices=SALES_LEVEL_CHOICES,
        default='medium',
        help_text="Expected sales level"
    )
    products = models.TextField(
        help_text="Associated products (e.g., 'Chocolate cakes, Heart-shaped cakes')"
    )
    expected_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Expected revenue for this event"
    )
    growth_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Expected growth rate percentage"
    )
    icon = models.CharField(
        max_length=20,
        choices=ICON_CHOICES,
        default='calendar',
        help_text="Icon to display for this event"
    )
    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default='blue',
        help_text="Color theme for this event"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this event is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'seasonal_events'
        ordering = ['month', 'day']
        unique_together = ['name', 'month', 'day', 'year']
    
    def __str__(self):
        return f"{self.name} ({self.month}/{self.day}/{self.year})"
    
    @property
    def event_date(self):
        """Return the event date as a date object"""
        try:
            return date(self.year, self.month, self.day)
        except ValueError:
            return None
    
    @property
    def formatted_date(self):
        """Return formatted date string"""
        if self.event_date:
            return self.event_date.strftime("%d %B")
        return f"{self.day} {self.get_month_name()}"
    
    def get_month_name(self):
        """Get month name from month number"""
        month_names = [
            '', 'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return month_names[self.month] if 1 <= self.month <= 12 else 'Unknown'
    
    def get_sales_color(self):
        """Get color code for sales level"""
        color_map = {
            'low': 'gray',
            'medium': 'yellow',
            'high': 'orange',
            'peak': 'red'
        }
        return color_map.get(self.sales_level, 'blue')
    
    def get_sales_bg_color(self):
        """Get background color for sales level"""
        bg_color_map = {
            'low': 'bg-gray-100',
            'medium': 'bg-yellow-100',
            'high': 'bg-orange-100',
            'peak': 'bg-red-100'
        }
        return bg_color_map.get(self.sales_level, 'bg-blue-100')