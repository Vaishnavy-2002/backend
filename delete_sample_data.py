#!/usr/bin/env python3
"""
Script to delete all sample data from the SweetBites database
This will remove sample data while preserving core system data like admin users
"""

import os
import sys
import django
from django.db import transaction

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sweetbite_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Q
from orders.models import Order, OrderItem, ShippingAddress, Payment, OrderStatusHistory, DeliveryLocationHistory
from cakes.models import Category, CakeSize, CakeShape, Frosting, Topping, Cake, CustomCake, Review
from inventory.models import Supplier, Ingredient, StockMovement, PurchaseOrder, PurchaseOrderItem, Recipe, RecipeIngredient
from offers.models import Offer
# from analytics.models import AnalyticsData  # This model doesn't exist
from seasonal_trends.models import SeasonalEvent

User = get_user_model()

def delete_sample_data():
    """Delete all sample data from the database"""
    
    print("🧹 Starting sample data cleanup...")
    
    with transaction.atomic():
        # 1. Delete sample orders and related data
        print("\n📦 Deleting sample orders...")
        sample_orders = Order.objects.filter(
            Q(order_number__startswith='SAMPLE-') |
            Q(order_number__startswith='TEST-') |
            Q(customer__username__startswith='test_') |
            Q(customer__email__endswith='@test.com')
        )
        order_count = sample_orders.count()
        sample_orders.delete()
        print(f"   ✅ Deleted {order_count} sample orders")
        
        # 2. Delete sample customers (but keep admin users)
        print("\n👥 Deleting sample customers...")
        sample_users = User.objects.filter(
            Q(username__startswith='test_') |
            Q(email__endswith='@test.com') |
            Q(first_name__startswith='Test') |
            Q(last_name__startswith='Customer')
        ).exclude(
            Q(is_superuser=True) |
            Q(username='admin') |
            Q(email='admin@admin.com')
        )
        user_count = sample_users.count()
        sample_users.delete()
        print(f"   ✅ Deleted {user_count} sample users")
        
        # 3. Delete sample cakes
        print("\n🎂 Deleting sample cakes...")
        sample_cakes = Cake.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test') |
            Q(description__startswith='Sample') |
            Q(description__startswith='Test')
        )
        cake_count = sample_cakes.count()
        sample_cakes.delete()
        print(f"   ✅ Deleted {cake_count} sample cakes")
        
        # 4. Delete sample ingredients
        print("\n🥚 Deleting sample ingredients...")
        sample_ingredients = Ingredient.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test') |
            Q(description__startswith='Sample') |
            Q(description__startswith='Test')
        )
        ingredient_count = sample_ingredients.count()
        sample_ingredients.delete()
        print(f"   ✅ Deleted {ingredient_count} sample ingredients")
        
        # 5. Delete sample suppliers
        print("\n🏢 Deleting sample suppliers...")
        sample_suppliers = Supplier.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test') |
            Q(contact_person__startswith='Test') |
            Q(email__endswith='@test.com')
        )
        supplier_count = sample_suppliers.count()
        sample_suppliers.delete()
        print(f"   ✅ Deleted {supplier_count} sample suppliers")
        
        # 6. Delete sample stock movements
        print("\n📊 Deleting sample stock movements...")
        sample_movements = StockMovement.objects.filter(
            Q(reference__startswith='SAMPLE-') |
            Q(reference__startswith='TEST-') |
            Q(notes__startswith='Sample') |
            Q(notes__startswith='Test')
        )
        movement_count = sample_movements.count()
        sample_movements.delete()
        print(f"   ✅ Deleted {movement_count} sample stock movements")
        
        # 7. Delete sample offers
        print("\n🎁 Deleting sample offers...")
        sample_offers = Offer.objects.filter(
            Q(title__startswith='Sample') |
            Q(title__startswith='Test') |
            Q(title__startswith='Promotion for') |
            Q(description__startswith='Sample') |
            Q(description__startswith='Test')
        )
        offer_count = sample_offers.count()
        sample_offers.delete()
        print(f"   ✅ Deleted {offer_count} sample offers")
        
        # 8. Delete sample seasonal events
        print("\n📅 Deleting sample seasonal events...")
        sample_events = SeasonalEvent.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test') |
            Q(description__startswith='Sample') |
            Q(description__startswith='Test')
        )
        event_count = sample_events.count()
        sample_events.delete()
        print(f"   ✅ Deleted {event_count} sample seasonal events")
        
        # 9. Skip analytics data (no AnalyticsData model exists)
        
        # 10. Delete sample reviews
        print("\n⭐ Deleting sample reviews...")
        sample_reviews = Review.objects.filter(
            Q(comment__startswith='Sample') |
            Q(comment__startswith='Test') |
            Q(user__username__startswith='test_')
        )
        review_count = sample_reviews.count()
        sample_reviews.delete()
        print(f"   ✅ Deleted {review_count} sample reviews")
        
        # 11. Skip custom cakes (no user field to filter by)
        
        # 12. Delete sample purchase orders
        print("\n🛒 Deleting sample purchase orders...")
        sample_purchase_orders = PurchaseOrder.objects.filter(
            Q(po_number__startswith='SAMPLE-') |
            Q(po_number__startswith='TEST-') |
            Q(supplier__name__startswith='Sample') |
            Q(supplier__name__startswith='Test')
        )
        po_count = sample_purchase_orders.count()
        sample_purchase_orders.delete()
        print(f"   ✅ Deleted {po_count} sample purchase orders")
        
        # 13. Delete sample recipes
        print("\n📖 Deleting sample recipes...")
        sample_recipes = Recipe.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test') |
            Q(description__startswith='Sample') |
            Q(description__startswith='Test')
        )
        recipe_count = sample_recipes.count()
        sample_recipes.delete()
        print(f"   ✅ Deleted {recipe_count} sample recipes")
        
        # 14. Clean up any remaining sample categories, sizes, shapes, etc.
        print("\n🏷️ Cleaning up sample categories and attributes...")
        
        # Delete sample categories
        sample_categories = Category.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test')
        )
        category_count = sample_categories.count()
        sample_categories.delete()
        print(f"   ✅ Deleted {category_count} sample categories")
        
        # Delete sample cake sizes
        sample_sizes = CakeSize.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test')
        )
        size_count = sample_sizes.count()
        sample_sizes.delete()
        print(f"   ✅ Deleted {size_count} sample cake sizes")
        
        # Delete sample cake shapes
        sample_shapes = CakeShape.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test')
        )
        shape_count = sample_shapes.count()
        sample_shapes.delete()
        print(f"   ✅ Deleted {shape_count} sample cake shapes")
        
        # Delete sample frostings
        sample_frostings = Frosting.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test')
        )
        frosting_count = sample_frostings.count()
        sample_frostings.delete()
        print(f"   ✅ Deleted {frosting_count} sample frostings")
        
        # Delete sample toppings
        sample_toppings = Topping.objects.filter(
            Q(name__startswith='Sample') |
            Q(name__startswith='Test')
        )
        topping_count = sample_toppings.count()
        sample_toppings.delete()
        print(f"   ✅ Deleted {topping_count} sample toppings")
    
    print("\n🎉 Sample data cleanup completed successfully!")
    print("\n📊 Summary of remaining data:")
    
    # Show remaining counts
    print(f"   👥 Users: {User.objects.count()}")
    print(f"   🎂 Cakes: {Cake.objects.count()}")
    print(f"   🥚 Ingredients: {Ingredient.objects.count()}")
    print(f"   🏢 Suppliers: {Supplier.objects.count()}")
    print(f"   📦 Orders: {Order.objects.count()}")
    print(f"   📊 Stock Movements: {StockMovement.objects.count()}")
    print(f"   🎁 Offers: {Offer.objects.count()}")
    print(f"   📅 Seasonal Events: {SeasonalEvent.objects.count()}")
    print(f"   ⭐ Reviews: {Review.objects.count()}")
    print(f"   🎨 Custom Cakes: {CustomCake.objects.count()}")
    print(f"   🛒 Purchase Orders: {PurchaseOrder.objects.count()}")
    print(f"   📖 Recipes: {Recipe.objects.count()}")
    print(f"   🏷️ Categories: {Category.objects.count()}")
    print(f"   📏 Cake Sizes: {CakeSize.objects.count()}")
    print(f"   🔷 Cake Shapes: {CakeShape.objects.count()}")
    print(f"   🧁 Frostings: {Frosting.objects.count()}")
    print(f"   🍓 Toppings: {Topping.objects.count()}")
    
    print("\n✅ Database is now clean and ready for real data!")

if __name__ == "__main__":
    try:
        delete_sample_data()
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        sys.exit(1)
