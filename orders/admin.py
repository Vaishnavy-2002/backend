from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, ShippingAddress, Payment

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer', 'order_type', 'order_status', 
        'payment_status', 'total_amount', 'created_at'
    ]
    list_filter = [
        'order_status', 'payment_status', 'order_type', 
        'created_at', 'delivery_date'
    ]
    search_fields = ['order_number', 'customer__username', 'customer__email']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'order_type', 'order_status')
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'payment_method', 'subtotal', 'tax', 'delivery_fee', 'total_amount')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'delivery_instructions', 'delivery_person', 'delivery_date', 'delivery_time')
        }),
        ('Staff Assignment', {
            'fields': ('assigned_staff',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'delivered_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'cake', 'quantity', 'unit_price', 'total_price']
    list_filter = ['cake__category']
    search_fields = ['order__order_number', 'cake__name']
    readonly_fields = ['total_price']

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'updated_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'first_name', 'last_name', 'city', 'state', 'is_default', 'created_at']
    list_filter = ['is_default', 'city', 'state', 'country']
    search_fields = ['customer__username', 'first_name', 'last_name', 'city']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_method', 'payment_status', 'amount', 'currency', 'payment_date']
    list_filter = ['payment_status', 'payment_method', 'currency']
    search_fields = ['order__order_number', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
