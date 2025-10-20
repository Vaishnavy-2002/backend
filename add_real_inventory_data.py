#!/usr/bin/env python
"""
Utility script to add real inventory data for testing
Run this script when you need to add actual inventory data for testing purposes
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sweetbite_backend.settings')
django.setup()

from inventory.models import Supplier, Ingredient, StockMovement
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

def add_real_inventory_data():
    """Add real inventory data for testing purposes"""
    
    print('📦 Adding Real Inventory Data...')
    
    # Get admin user
    admin_user = User.objects.filter(user_type='admin').first()
    if not admin_user:
        print('❌ No admin user found. Please create an admin user first.')
        return
    
    # Create real suppliers
    suppliers_data = [
        {
            'name': 'Fresh Ingredients Co.',
            'contact_person': 'John Smith',
            'email': 'john@fresh.com',
            'phone': '+1-555-0101',
            'address': '123 Fresh Street, Food City',
            'notes': 'Primary supplier for basic ingredients'
        },
        {
            'name': 'Premium Supplies Ltd.',
            'contact_person': 'Sarah Johnson',
            'email': 'sarah@premium.com',
            'phone': '+1-555-0102',
            'address': '456 Premium Avenue, Quality Town',
            'notes': 'High-quality ingredients supplier'
        },
        {
            'name': 'Quality Foods Inc.',
            'contact_person': 'Mike Brown',
            'email': 'mike@quality.com',
            'phone': '+1-555-0103',
            'address': '789 Quality Road, Excellence City',
            'notes': 'Specialty ingredients supplier'
        },
    ]
    
    suppliers = []
    for supplier_data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            name=supplier_data['name'],
            defaults=supplier_data
        )
        suppliers.append(supplier)
        if created:
            print(f'✅ Created supplier: {supplier.name}')
        else:
            print(f'ℹ️ Supplier already exists: {supplier.name}')
    
    # Create real ingredients
    ingredients_data = [
        {
            'name': 'All-Purpose Flour',
            'description': 'High-quality all-purpose flour for baking',
            'unit': 'kg',
            'current_stock': 25.0,
            'minimum_stock': 5.0,
            'unit_cost': 2.50,
            'supplier': suppliers[0],
            'location': 'Storage Room A'
        },
        {
            'name': 'Granulated Sugar',
            'description': 'Fine granulated sugar for baking and cooking',
            'unit': 'kg',
            'current_stock': 15.0,
            'minimum_stock': 3.0,
            'unit_cost': 3.00,
            'supplier': suppliers[0],
            'location': 'Storage Room A'
        },
        {
            'name': 'Unsalted Butter',
            'description': 'Premium unsalted butter for baking',
            'unit': 'kg',
            'current_stock': 8.0,
            'minimum_stock': 2.0,
            'unit_cost': 8.50,
            'supplier': suppliers[1],
            'location': 'Refrigerator'
        },
        {
            'name': 'Fresh Eggs',
            'description': 'Farm-fresh eggs for baking',
            'unit': 'pcs',
            'current_stock': 120.0,
            'minimum_stock': 30.0,
            'unit_cost': 0.30,
            'supplier': suppliers[1],
            'location': 'Refrigerator'
        },
        {
            'name': 'Pure Vanilla Extract',
            'description': 'Pure vanilla extract for flavoring',
            'unit': 'ml',
            'current_stock': 250.0,
            'minimum_stock': 50.0,
            'unit_cost': 0.05,
            'supplier': suppliers[2],
            'location': 'Spice Cabinet'
        },
        {
            'name': 'Dark Chocolate Chips',
            'description': 'Premium dark chocolate chips',
            'unit': 'kg',
            'current_stock': 5.0,
            'minimum_stock': 1.0,
            'unit_cost': 12.00,
            'supplier': suppliers[2],
            'location': 'Storage Room B'
        },
        {
            'name': 'Baking Powder',
            'description': 'Double-acting baking powder',
            'unit': 'g',
            'current_stock': 500.0,
            'minimum_stock': 100.0,
            'unit_cost': 0.02,
            'supplier': suppliers[0],
            'location': 'Spice Cabinet'
        },
        {
            'name': 'Sea Salt',
            'description': 'Fine sea salt for seasoning',
            'unit': 'g',
            'current_stock': 1000.0,
            'minimum_stock': 200.0,
            'unit_cost': 0.01,
            'supplier': suppliers[0],
            'location': 'Spice Cabinet'
        },
    ]
    
    ingredients = []
    for ingredient_data in ingredients_data:
        ingredient, created = Ingredient.objects.get_or_create(
            name=ingredient_data['name'],
            defaults=ingredient_data
        )
        ingredients.append(ingredient)
        if created:
            print(f'✅ Created ingredient: {ingredient.name}')
        else:
            print(f'ℹ️ Ingredient already exists: {ingredient.name}')
    
    print(f'\\n📊 Created {len(suppliers)} suppliers and {len(ingredients)} ingredients')
    print('\\n💡 To add stock movements and test the analytics:')
    print('   1. Go to the inventory dashboard')
    print('   2. Add some stock movements (in/out/waste)')
    print('   3. The analytics will show real data based on your movements')
    
    return suppliers, ingredients

if __name__ == '__main__':
    add_real_inventory_data()
