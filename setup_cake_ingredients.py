"""
Script to set up ingredient data for existing cakes
This will populate the ingredients field for cakes so they can be used for automatic deduction
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sweetbite_backend.settings')
django.setup()

from cakes.models import Cake
from inventory.models import Ingredient


def setup_cake_ingredients():
    """
    Set up ingredient data for existing cakes
    """
    print("🍰 Setting up ingredient data for cakes...")
    
    # Sample ingredients for different cake types
    sample_ingredients = {
        'chocolate': [
            {'name': 'Flour', 'quantity': 0.5, 'unit': 'kg'},
            {'name': 'Sugar', 'quantity': 0.3, 'unit': 'kg'},
            {'name': 'Butter', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Eggs', 'quantity': 3, 'unit': 'pcs'},
            {'name': 'Chocolate Chips', 'quantity': 0.1, 'unit': 'kg'},
            {'name': 'Baking Powder', 'quantity': 10, 'unit': 'g'},
        ],
        'vanilla': [
            {'name': 'Flour', 'quantity': 0.5, 'unit': 'kg'},
            {'name': 'Sugar', 'quantity': 0.3, 'unit': 'kg'},
            {'name': 'Butter', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Eggs', 'quantity': 3, 'unit': 'pcs'},
            {'name': 'Vanilla Extract', 'quantity': 10, 'unit': 'ml'},
            {'name': 'Baking Powder', 'quantity': 10, 'unit': 'g'},
        ],
        'strawberry': [
            {'name': 'Flour', 'quantity': 0.5, 'unit': 'kg'},
            {'name': 'Sugar', 'quantity': 0.3, 'unit': 'kg'},
            {'name': 'Butter', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Eggs', 'quantity': 3, 'unit': 'pcs'},
            {'name': 'Strawberries', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Baking Powder', 'quantity': 10, 'unit': 'g'},
        ],
        'fruit': [
            {'name': 'Flour', 'quantity': 0.5, 'unit': 'kg'},
            {'name': 'Sugar', 'quantity': 0.3, 'unit': 'kg'},
            {'name': 'Butter', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Eggs', 'quantity': 3, 'unit': 'pcs'},
            {'name': 'Mixed Fruits', 'quantity': 0.3, 'unit': 'kg'},
            {'name': 'Baking Powder', 'quantity': 10, 'unit': 'g'},
        ],
        'mousse': [
            {'name': 'Flour', 'quantity': 0.3, 'unit': 'kg'},
            {'name': 'Sugar', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Butter', 'quantity': 0.1, 'unit': 'kg'},
            {'name': 'Eggs', 'quantity': 2, 'unit': 'pcs'},
            {'name': 'Cream', 'quantity': 0.3, 'unit': 'l'},
            {'name': 'Gelatin', 'quantity': 5, 'unit': 'g'},
        ],
        'cup': [
            {'name': 'Flour', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Sugar', 'quantity': 0.15, 'unit': 'kg'},
            {'name': 'Butter', 'quantity': 0.1, 'unit': 'kg'},
            {'name': 'Eggs', 'quantity': 2, 'unit': 'pcs'},
            {'name': 'Baking Powder', 'quantity': 5, 'unit': 'g'},
        ]
    }
    
    # Get all cakes
    cakes = Cake.objects.all()
    print(f"Found {cakes.count()} cakes to update")
    
    updated_count = 0
    
    for cake in cakes:
        cake_name_lower = cake.name.lower()
        
        # Determine which ingredient set to use based on cake name
        ingredients_to_use = None
        for key, ingredients in sample_ingredients.items():
            if key in cake_name_lower:
                ingredients_to_use = ingredients
                break
        
        # If no specific match, use chocolate as default
        if not ingredients_to_use:
            ingredients_to_use = sample_ingredients['chocolate']
        
        # Update the cake with ingredients
        cake.ingredients = ingredients_to_use
        cake.save()
        
        print(f"✅ Updated '{cake.name}' with {len(ingredients_to_use)} ingredients")
        updated_count += 1
    
    print(f"\n🎉 Successfully updated {updated_count} cakes with ingredient data!")
    
    # Verify ingredients exist in database
    print("\n🔍 Verifying ingredients in database...")
    all_ingredient_names = set()
    for ingredients in sample_ingredients.values():
        for ingredient in ingredients:
            all_ingredient_names.add(ingredient['name'])
    
    missing_ingredients = []
    for ingredient_name in all_ingredient_names:
        if not Ingredient.objects.filter(name__iexact=ingredient_name).exists():
            missing_ingredients.append(ingredient_name)
    
    if missing_ingredients:
        print(f"⚠️  Missing ingredients in database: {', '.join(missing_ingredients)}")
        print("Please add these ingredients to the inventory system first.")
    else:
        print("✅ All required ingredients exist in the database!")


def test_ingredient_deduction():
    """
    Test the ingredient deduction functionality
    """
    print("\n🧪 Testing ingredient deduction...")
    
    # Get a cake with ingredients
    cake = Cake.objects.filter(ingredients__isnull=False).first()
    if not cake:
        print("❌ No cakes with ingredients found!")
        return
    
    print(f"Testing with cake: {cake.name}")
    print(f"Ingredients: {cake.ingredients}")
    
    # Check current stock levels
    print("\nCurrent stock levels:")
    for ingredient_data in cake.ingredients:
        ingredient_name = ingredient_data['name']
        try:
            ingredient = Ingredient.objects.get(name__iexact=ingredient_name)
            print(f"  {ingredient_name}: {ingredient.current_stock} {ingredient.unit}")
        except Ingredient.DoesNotExist:
            print(f"  {ingredient_name}: NOT FOUND")


if __name__ == '__main__':
    setup_cake_ingredients()
    test_ingredient_deduction()
