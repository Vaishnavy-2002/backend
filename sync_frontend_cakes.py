#!/usr/bin/env python
"""
Sync the frontend cakes.js data with the database
This will create all the cakes that the frontend expects
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sweetbite_backend.settings')
django.setup()

from cakes.models import Cake, Category

def create_categories():
    """Create categories needed for the cakes"""
    categories_data = [
        {'name': 'Chocolate', 'description': 'Rich chocolate cakes'},
        {'name': 'Vanilla', 'description': 'Classic vanilla cakes'},
        {'name': 'Red Velvet', 'description': 'Southern classic red velvet cakes'},
        {'name': 'Fruit', 'description': 'Fresh fruit cakes'},
        {'name': 'Carrot', 'description': 'Spiced carrot cakes'},
        {'name': 'Citrus', 'description': 'Tangy citrus cakes'},
        {'name': 'Specialty', 'description': 'Special occasion cakes'},
    ]
    
    print("📁 Creating Categories...")
    created_categories = {}
    
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        created_categories[cat_data['name'].lower().replace(' ', '-')] = category
        if created:
            print(f"✅ Created category: {category.name}")
        else:
            print(f"⚠️  Category exists: {category.name}")
    
    return created_categories

def sync_cakes():
    """Create cakes that match the frontend data"""
    categories = create_categories()
    
    # Map frontend categories to database categories
    category_mapping = {
        'chocolate': categories.get('chocolate'),
        'vanilla': categories.get('vanilla'),
        'red-velvet': categories.get('red-velvet'),
        'fruit': categories.get('fruit'),
        'carrot': categories.get('carrot'),
        'citrus': categories.get('citrus'),
    }
    
    # Frontend cakes data (matching cakes.js)
    frontend_cakes = [
        {
            'id': 1,
            'name': 'Chocolate Dream Cake',
            'description': 'Rich chocolate cake layered with chocolate ganache and topped with chocolate shavings',
            'price': Decimal('2450.99'),
            'category': 'chocolate',
        },
        {
            'id': 2,
            'name': 'Vanilla Delight',
            'description': 'Classic vanilla cake with buttercream frosting and fresh berries',
            'price': Decimal('2150.99'),
            'category': 'vanilla',
        },
        {
            'id': 3,
            'name': 'Red Velvet Supreme',
            'description': 'Southern classic red velvet cake with cream cheese frosting',
            'price': Decimal('2350.99'),
            'category': 'red-velvet',
        },
        {
            'id': 4,
            'name': 'Strawberry Shortcake',
            'description': 'Light sponge cake with fresh strawberries and whipped cream',
            'price': Decimal('2200.99'),
            'category': 'fruit',
        },
        {
            'id': 5,
            'name': 'Carrot Cake Delight',
            'description': 'Moist carrot cake with walnuts and cream cheese frosting',
            'price': Decimal('2250.99'),
            'category': 'carrot',
        },
        {
            'id': 6,
            'name': 'Lemon Zest Cake',
            'description': 'Tangy lemon cake with lemon curd filling and citrus glaze',
            'price': Decimal('2100.99'),
            'category': 'citrus',
        }
    ]
    
    print("\n🍰 Syncing Cakes with Frontend...")
    print("=" * 50)
    
    created_count = 0
    updated_count = 0
    
    for cake_data in frontend_cakes:
        category = category_mapping.get(cake_data['category'])
        
        if not category:
            print(f"❌ No category found for {cake_data['category']}")
            continue
        
        # Check if cake exists with this ID
        try:
            existing_cake = Cake.objects.get(id=cake_data['id'])
            # Update existing cake
            existing_cake.name = cake_data['name']
            existing_cake.description = cake_data['description']
            existing_cake.price = cake_data['price']
            existing_cake.category = category
            existing_cake.image = 'cakes/default.jpg'  # Default image
            existing_cake.save()
            print(f"✅ Updated: {existing_cake.name} (ID: {existing_cake.id})")
            updated_count += 1
            
        except Cake.DoesNotExist:
            # Create new cake with specific ID
            cake = Cake(
                id=cake_data['id'],  # Set specific ID
                name=cake_data['name'],
                description=cake_data['description'],
                price=cake_data['price'],
                category=category,
                image='cakes/default.jpg'
            )
            cake.save()
            print(f"✅ Created: {cake.name} (ID: {cake.id})")
            created_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  Created: {created_count} cakes")
    print(f"  Updated: {updated_count} cakes")
    print(f"  Total cakes in database: {Cake.objects.count()}")
    
    return True

def main():
    print("🔄 Syncing Frontend Cakes with Database")
    print("=" * 60)
    print("This will ensure all frontend cakes exist in the database")
    print()
    
    success = sync_cakes()
    
    if success:
        print("\n✅ SUCCESS! All frontend cakes are now in the database")
        print("🚀 Your place order button should work now!")
        
        # Show final cake list
        print("\n🍰 Available Cakes:")
        cakes = Cake.objects.all().order_by('id')
        for cake in cakes:
            print(f"  ID: {cake.id} - {cake.name} - RS {cake.price}")
    else:
        print("\n❌ Some issues occurred during sync")

if __name__ == "__main__":
    main()
