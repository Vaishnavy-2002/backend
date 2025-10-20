from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Offer

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'offer_type', 
        'status', 
        'discount_display', 
        'validity_period', 
        'is_homepage_featured',
        'is_popup',
        'usage_count',
        'created_at'
    ]
    
    list_filter = [
        'status', 
        'offer_type', 
        'is_homepage_featured', 
        'is_popup',
        'created_at',
        'start_date',
        'end_date'
    ]
    
    search_fields = ['title', 'description']
    
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'offer_type', 'status')
        }),
        ('Offer Details', {
            'fields': (
                'discount_percentage', 
                'discount_amount', 
                'minimum_order_amount',
                'max_usage'
            )
        }),
        ('Validity Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Display Settings', {
            'fields': (
                'banner_image',
                'background_color',
                'text_color',
                'is_homepage_featured',
                'is_popup'
            )
        }),
        ('Targeting', {
            'fields': ('target_user_types',)
        }),
        ('Tracking', {
            'fields': ('usage_count', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def discount_display(self, obj):
        """Display discount information"""
        if obj.offer_type == 'percentage' and obj.discount_percentage:
            return f"{obj.discount_percentage}% OFF"
        elif obj.offer_type == 'fixed' and obj.discount_amount:
            return f"RS {obj.discount_amount} OFF"
        elif obj.offer_type == 'free_delivery':
            return "FREE DELIVERY"
        elif obj.offer_type == 'buy_one_get_one':
            return "BUY 1 GET 1"
        else:
            return "SPECIAL OFFER"
    discount_display.short_description = 'Discount'
    
    def validity_period(self, obj):
        """Display validity period with status"""
        now = timezone.now()
        if obj.is_expired:
            return format_html(
                '<span style="color: red;">EXPIRED</span><br>'
                '<small>Ended: {}</small>',
                obj.end_date.strftime('%Y-%m-%d %H:%M')
            )
        elif obj.start_date > now:
            return format_html(
                '<span style="color: orange;">UPCOMING</span><br>'
                '<small>Starts: {}</small>',
                obj.start_date.strftime('%Y-%m-%d %H:%M')
            )
        elif obj.is_active:
            return format_html(
                '<span style="color: green;">ACTIVE</span><br>'
                '<small>Ends: {}</small>',
                obj.end_date.strftime('%Y-%m-%d %H:%M')
            )
        else:
            return format_html(
                '<span style="color: gray;">INACTIVE</span>'
            )
    validity_period.short_description = 'Validity'
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user"""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_offers', 'deactivate_offers', 'mark_as_expired']
    
    def activate_offers(self, request, queryset):
        """Activate selected offers"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} offers activated successfully.')
    activate_offers.short_description = "Activate selected offers"
    
    def deactivate_offers(self, request, queryset):
        """Deactivate selected offers"""
        updated = queryset.update(status='paused')
        self.message_user(request, f'{updated} offers deactivated successfully.')
    deactivate_offers.short_description = "Deactivate selected offers"
    
    def mark_as_expired(self, request, queryset):
        """Mark selected offers as expired"""
        updated = queryset.update(status='expired')
        self.message_user(request, f'{updated} offers marked as expired.')
    mark_as_expired.short_description = "Mark selected offers as expired"
