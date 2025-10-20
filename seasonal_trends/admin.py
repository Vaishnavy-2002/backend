from django.contrib import admin
from .models import SeasonalEvent


@admin.register(SeasonalEvent)
class SeasonalEventAdmin(admin.ModelAdmin):
    """Admin interface for SeasonalEvent model"""
    
    list_display = [
        'name', 'formatted_date', 'year', 'sales_level', 
        'expected_revenue', 'growth_rate', 'is_active'
    ]
    list_filter = [
        'year', 'month', 'sales_level', 'is_active', 'icon', 'color'
    ]
    search_fields = ['name', 'description', 'products']
    list_editable = ['is_active']
    ordering = ['year', 'month', 'day']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('name', 'description', 'month', 'day', 'year')
        }),
        ('Sales Data', {
            'fields': ('sales_level', 'expected_revenue', 'growth_rate', 'products')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'is_active')
        }),
    )
    
    def formatted_date(self, obj):
        """Display formatted date in admin list"""
        return obj.formatted_date
    formatted_date.short_description = 'Date'