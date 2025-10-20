from django.contrib import admin
from .models import POSSession, QuickSale, QuickSaleItem, Customer, DailySales

@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cashier', 'start_time', 'end_time', 'status', 
        'total_sales', 'total_transactions'
    ]
    list_filter = ['status', 'start_time', 'cashier']
    search_fields = ['cashier__username', 'notes']
    readonly_fields = ['start_time', 'end_time', 'total_sales', 'total_transactions']
    date_hierarchy = 'start_time'
    ordering = ['-start_time']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('cashier', 'status', 'start_time', 'end_time')
        }),
        ('Financial Information', {
            'fields': ('opening_amount', 'closing_amount', 'total_sales', 'total_transactions')
        }),
        ('Notes', {
            'fields': ('notes',)
        })
    )

@admin.register(QuickSale)
class QuickSaleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session', 'customer_name', 'customer_phone', 
        'total_amount', 'payment_method', 'created_at'
    ]
    list_filter = ['payment_method', 'created_at', 'session__cashier']
    search_fields = ['customer_name', 'customer_phone', 'session__cashier__username']
    readonly_fields = ['subtotal', 'tax', 'total_amount', 'change_amount', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Sale Information', {
            'fields': ('session', 'customer_name', 'customer_phone')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'tax', 'discount', 'total_amount', 'amount_paid', 'change_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(QuickSaleItem)
class QuickSaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'cake', 'quantity', 'unit_price', 'total_price']
    list_filter = ['cake__category', 'sale__payment_method']
    search_fields = ['sale__customer_name', 'cake__name']
    readonly_fields = ['total_price']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'phone', 'email', 'total_orders', 'total_spent', 
        'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['total_orders', 'total_spent', 'created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'phone', 'email', 'address')
        }),
        ('Statistics', {
            'fields': ('total_orders', 'total_spent'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(DailySales)
class DailySalesAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_sales', 'total_transactions', 'cash_sales', 
        'card_sales', 'mobile_sales', 'average_order_value'
    ]
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['average_order_value']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Sales Summary', {
            'fields': ('total_sales', 'total_transactions', 'average_order_value')
        }),
        ('Payment Breakdown', {
            'fields': ('cash_sales', 'card_sales', 'mobile_sales')
        })
    )
