#!/usr/bin/env python
"""
Create test cakes for order testing
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sweetbite_backend.settings')
django.setup()

from cakes.models import Cake, Category

def create_test_categories():
    """Create test categories first"""
    print('📁 Creating Test Categories')
    print('=' * 30)
    
    categories_data = [
        {'name': 'Chocolate', 'description': 'Rich chocolate cakes', 'icon': '🍫'},
        {'name': 'Vanilla', 'description': 'Classic vanilla cakes', 'icon': '🍰'},
        {'name': 'Fruit', 'description': 'Fresh fruit cakes', 'icon': '🍓'},
        {'name': 'Specialty', 'description': 'Special occasion cakes', 'icon': '✨'},
    ]
    
    created_count = 0
    for cat_data in categories_data:
        if not Category.objects.filter(name=cat_data['name']).exists():
            try:
                category = Category.objects.create(**cat_data)
                print(f'✅ Created category: {category.name}')
                created_count += 1
            except Exception as e:
                print(f'❌ Error creating {cat_data["name"]}: {e}')
        else:
            print(f'⚠️  Category already exists: {cat_data["name"]}')
    
    print(f'Categories created: {created_count}')
    return Category.objects.all()

def create_test_cakes():
    """Create test cakes if they don't exist"""
    print('🍰 Creating Test Cakes')
    print('=' * 30)
    
    # Get categories
    categories = {cat.name.lower(): cat for cat in Category.objects.all()}
    
    if not categories:
        print('❌ No categories found. Create categories first.')
        return False
    
    # Test cakes data
    cakes_data = [
        {
            'name': 'Chocolate Cake',
            'description': 'Rich and moist chocolate cake with chocolate frosting',
            'price': 25.99,
            'category': categories.get('chocolate'),
            'image': 'cakes/chocolate_cake.jpg'
        },
        {
            'name': 'Vanilla Cake',
            'description': 'Classic vanilla sponge cake with vanilla buttercream',
            'price': 22.99,
            'category': categories.get('vanilla'),
            'image': 'cakes/vanilla_cake.jpg'
        },
        {
            'name': 'Strawberry Cake',
            'description': 'Fresh strawberry cake with strawberry frosting',
            'price': 28.99,
            'category': categories.get('fruit'),
            'image': 'cakes/strawberry_cake.jpg'
        },
        {
            'name': 'Red Velvet Cake',
            'description': 'Smooth red velvet cake with cream cheese frosting',
            'price': 32.99,
            'category': categories.get('specialty'),
            'image': 'cakes/red_velvet_cake.jpg'
        },
        {
            'name': 'Carrot Cake',
            'description': 'Spiced carrot cake with cream cheese frosting',
            'price': 29.99,
            'category': categories.get('specialty'),
            'image': 'cakes/carrot_cake.jpg'
        }
    ]
    
    created_count = 0
    existing_count = 0
    
    for cake_data in cakes_data:
        if not Cake.objects.filter(name=cake_data['name']).exists():
            try:
                cake = Cake.objects.create(**cake_data)
                print(f'✅ Created: {cake.name} - ${cake.price}')
                created_count += 1
            except Exception as e:
                print(f'❌ Error creating {cake_data["name"]}: {e}')
        else:
            print(f'⚠️  Already exists: {cake_data["name"]}')
            existing_count += 1
    
    print(f'\n📊 Summary:')
    print(f'  New cakes created: {created_count}')
    print(f'  Existing cakes: {existing_count}')
    print(f'  Total cakes in database: {Cake.objects.count()}')
    
    return Cake.objects.count() > 0

if __name__ == "__main__":
    # First create categories
    categories = create_test_categories()
    
    # Then create cakes
    success = create_test_cakes()
    if success:
        print('\n✅ Test cakes are ready for order testing!')
    else:
        print('\n❌ Failed to create test cakes')
