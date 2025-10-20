from django.contrib import admin
from .models import Category, Cake, CustomCake, CakeSize, CakeShape, Frosting, Topping

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')

@admin.register(Cake)
class CakeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'rating', 'created_at')
    list_filter = ('category', 'is_available', 'is_customizable', 'created_at')
    search_fields = ('name', 'description', 'ingredients')

@admin.register(CustomCake)
class CustomCakeAdmin(admin.ModelAdmin):
    list_display = ('base_cake', 'size', 'shape', 'total_price', 'created_at')
    list_filter = ('size', 'shape', 'created_at')
    search_fields = ('base_cake__name', 'custom_message')

@admin.register(CakeSize)
class CakeSizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_modifier', 'is_active')
    list_filter = ('is_active',)

@admin.register(CakeShape)
class CakeShapeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_modifier', 'is_active')
    list_filter = ('is_active',)

@admin.register(Frosting)
class FrostingAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_modifier', 'is_active')
    list_filter = ('is_active',)

@admin.register(Topping)
class ToppingAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_modifier', 'is_active')
    list_filter = ('is_active',)


