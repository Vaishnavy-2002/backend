#!/usr/bin/env python
"""
Update customization options with new price modifiers (900-1900)
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sweetbite_backend.settings')
django.setup()

from cakes.models import CakeSize, CakeShape, Frosting, Topping

def update_customization_options():
    """Update all customization options with new price modifiers"""
    
    print("🔄 Updating Customization Options")
    print("=" * 50)
    
    # Update Cake Sizes
    print("\n📏 Updating Cake Sizes...")
    sizes_data = [
        {'id': 1, 'name': '6 inch', 'servings': 6, 'price_modifier': Decimal('0')},
        {'id': 2, 'name': '8 inch', 'servings': 12, 'price_modifier': Decimal('600')},
        {'id': 3, 'name': '10 inch', 'servings': 20, 'price_modifier': Decimal('800')},
        {'id': 4, 'name': '12 inch', 'servings': 30, 'price_modifier': Decimal('1000')}
    ]
    
    for size_data in sizes_data:
        try:
            size, created = CakeSize.objects.get_or_create(
                id=size_data['id'],
                defaults=size_data
            )
            if not created:
                size.name = size_data['name']
                size.servings = size_data['servings']
                size.price_modifier = size_data['price_modifier']
                size.save()
                print(f"✅ Updated: {size.name} - +${size.price_modifier}")
            else:
                print(f"✅ Created: {size.name} - +${size.price_modifier}")
        except Exception as e:
            print(f"❌ Error updating size {size_data['name']}: {e}")
    
    # Update Cake Shapes
    print("\n🔷 Updating Cake Shapes...")
    shapes_data = [
        {'id': 1, 'name': 'Round', 'price_modifier': Decimal('0')},
        {'id': 2, 'name': 'Square', 'price_modifier': Decimal('500')},
        {'id': 3, 'name': 'Heart', 'price_modifier': Decimal('700')},
        {'id': 4, 'name': 'Rectangle', 'price_modifier': Decimal('600')}
    ]
    
    for shape_data in shapes_data:
        try:
            shape, created = CakeShape.objects.get_or_create(
                id=shape_data['id'],
                defaults=shape_data
            )
            if not created:
                shape.name = shape_data['name']
                shape.price_modifier = shape_data['price_modifier']
                shape.save()
                print(f"✅ Updated: {shape.name} - +${shape.price_modifier}")
            else:
                print(f"✅ Created: {shape.name} - +${shape.price_modifier}")
        except Exception as e:
            print(f"❌ Error updating shape {shape_data['name']}: {e}")
    
    # Update Frostings
    print("\n🎨 Updating Frostings...")
    frostings_data = [
        {'id': 1, 'name': 'Buttercream', 'price_modifier': Decimal('0'), 'color': '#FFF8DC'},
        {'id': 2, 'name': 'Cream Cheese', 'price_modifier': Decimal('650'), 'color': '#FFF8DC'},
        {'id': 3, 'name': 'Chocolate Ganache', 'price_modifier': Decimal('800'), 'color': '#8B4513'},
        {'id': 4, 'name': 'Whipped Cream', 'price_modifier': Decimal('550'), 'color': '#FFFFFF'},
        {'id': 5, 'name': 'Red Velvet', 'price_modifier': Decimal('700'), 'color': '#DC143C'}
    ]
    
    for frosting_data in frostings_data:
        try:
            frosting, created = Frosting.objects.get_or_create(
                id=frosting_data['id'],
                defaults=frosting_data
            )
            if not created:
                frosting.name = frosting_data['name']
                frosting.price_modifier = frosting_data['price_modifier']
                frosting.color = frosting_data['color']
                frosting.save()
                print(f"✅ Updated: {frosting.name} - +${frosting.price_modifier}")
            else:
                print(f"✅ Created: {frosting.name} - +${frosting.price_modifier}")
        except Exception as e:
            print(f"❌ Error updating frosting {frosting_data['name']}: {e}")
    
    # Update Toppings
    print("\n🍓 Updating Toppings...")
    toppings_data = [
        {'id': 1, 'name': 'Fresh Berries', 'price_modifier': Decimal('900')},
        {'id': 2, 'name': 'Chocolate Shavings', 'price_modifier': Decimal('750')},
        {'id': 3, 'name': 'Sprinkles', 'price_modifier': Decimal('500')},
        {'id': 4, 'name': 'Edible Flowers', 'price_modifier': Decimal('1200')},
        {'id': 5, 'name': 'Nuts', 'price_modifier': Decimal('650')}
    ]
    
    for topping_data in toppings_data:
        try:
            topping, created = Topping.objects.get_or_create(
                id=topping_data['id'],
                defaults=topping_data
            )
            if not created:
                topping.name = topping_data['name']
                topping.price_modifier = topping_data['price_modifier']
                topping.save()
                print(f"✅ Updated: {topping.name} - +${topping.price_modifier}")
            else:
                print(f"✅ Created: {topping.name} - +${topping.price_modifier}")
        except Exception as e:
            print(f"❌ Error updating topping {topping_data['name']}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"  Cake Sizes: {CakeSize.objects.count()}")
    print(f"  Cake Shapes: {CakeShape.objects.count()}")
    print(f"  Frostings: {Frosting.objects.count()}")
    print(f"  Toppings: {Topping.objects.count()}")
    
    return True

def main():
    print("🔄 Updating Customization Options with New Prices")
    print("=" * 60)
    print("All customization options will have price modifiers between 500-1200")
    print()
    
    success = update_customization_options()
    
    if success:
        print("\n✅ SUCCESS! All customization options updated")
        print("🎂 Your customization prices are now between 500-1200!")
        
        # Show final customization options
        print("\n📋 Updated Customization Options:")
        print("\n📏 Cake Sizes:")
        for size in CakeSize.objects.all().order_by('id'):
            print(f"  {size.name}: +${size.price_modifier}")
        
        print("\n🔷 Cake Shapes:")
        for shape in CakeShape.objects.all().order_by('id'):
            print(f"  {shape.name}: +${shape.price_modifier}")
        
        print("\n🎨 Frostings:")
        for frosting in Frosting.objects.all().order_by('id'):
            print(f"  {frosting.name}: +${frosting.price_modifier}")
        
        print("\n🍓 Toppings:")
        for topping in Topping.objects.all().order_by('id'):
            print(f"  {topping.name}: +${topping.price_modifier}")
    else:
        print("\n❌ Some issues occurred during update")

if __name__ == "__main__":
    main()
