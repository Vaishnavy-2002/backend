from django.contrib import admin
from .models import (
    Supplier, Ingredient, StockMovement, 
    PurchaseOrder, PurchaseOrderItem, Recipe, RecipeIngredient
)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email']
    ordering = ['name']

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'current_stock', 'unit', 'unit_cost', 
        'minimum_stock', 'is_low_stock', 'is_active'
    ]
    list_filter = ['unit', 'is_active', 'supplier']
    search_fields = ['name', 'description']
    readonly_fields = ['total_value', 'is_low_stock']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'unit')
        }),
        ('Stock Information', {
            'fields': ('current_stock', 'minimum_stock', 'unit_cost', 'total_value', 'is_low_stock')
        }),
        ('Supplier Information', {
            'fields': ('supplier', 'location', 'expiry_date')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'ingredient', 'movement_type', 'quantity', 'previous_stock', 
        'new_stock', 'total_value', 'created_by', 'created_at'
    ]
    list_filter = ['movement_type', 'created_at']
    search_fields = ['ingredient__name', 'reference', 'notes']
    readonly_fields = ['previous_stock', 'new_stock', 'total_value', 'created_by', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number', 'supplier', 'status', 'order_date', 
        'total_amount', 'created_by'
    ]
    list_filter = ['status', 'order_date', 'supplier']
    search_fields = ['po_number', 'supplier__name']
    readonly_fields = ['po_number', 'created_by', 'created_at', 'updated_at']
    date_hierarchy = 'order_date'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('po_number', 'supplier', 'status', 'order_date')
        }),
        ('Delivery Information', {
            'fields': ('expected_delivery', 'delivery_date')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'tax', 'total_amount')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'ingredient', 'quantity', 'unit_cost', 'total_cost', 'received_quantity']
    list_filter = ['purchase_order__status']
    search_fields = ['purchase_order__po_number', 'ingredient__name']
    readonly_fields = ['total_cost']

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'servings', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'quantity', 'unit']
    list_filter = ['recipe']
    search_fields = ['recipe__name', 'ingredient__name']
