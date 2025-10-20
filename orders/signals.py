"""
Signals for automatic ingredient deduction when orders are created
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

from orders.models import Order, OrderItem
from inventory.models import Ingredient, StockMovement
from cakes.models import Cake

User = get_user_model()


@receiver(post_save, sender=Order)
def deduct_ingredients_on_order_confirmation(sender, instance, created, **kwargs):
    """
    Automatically deduct ingredients when an order is confirmed
    """
    # Only process when order status changes to 'confirmed' or 'preparing'
    if instance.order_status in ['confirmed', 'preparing']:
        # Check if we've already processed this order
        if hasattr(instance, '_ingredients_deducted'):
            return
        
        # Get a system user for stock movements (admin or inventory manager)
        system_user = User.objects.filter(
            user_type__in=['admin', 'inventory_manager']
        ).first()
        
        if not system_user:
            print("Warning: No admin or inventory manager found for stock movements")
            return
        
        # Process each order item
        for order_item in instance.items.all():
            deduct_ingredients_for_cake(
                cake=order_item.cake,
                quantity=order_item.quantity,
                order=instance,
                system_user=system_user
            )
        
        # Mark this order as processed
        instance._ingredients_deducted = True


def deduct_ingredients_for_cake(cake, quantity, order, system_user):
    """
    Deduct ingredients for a specific cake order
    """
    try:
        # Get ingredients from cake's ingredients field
        cake_ingredients = cake.ingredients if cake.ingredients else []
        
        if not cake_ingredients:
            print(f"Warning: No ingredients defined for cake '{cake.name}'")
            return
        
        # Process each ingredient
        for ingredient_data in cake_ingredients:
            ingredient_name = ingredient_data.get('name', '')
            ingredient_quantity = ingredient_data.get('quantity', 0)
            ingredient_unit = ingredient_data.get('unit', 'kg')
            
            if not ingredient_name or ingredient_quantity <= 0:
                continue
            
            # Find the ingredient in the database
            try:
                ingredient = Ingredient.objects.get(name__iexact=ingredient_name)
            except Ingredient.DoesNotExist:
                print(f"Warning: Ingredient '{ingredient_name}' not found in database")
                continue
            except Ingredient.MultipleObjectsReturned:
                print(f"Warning: Multiple ingredients found for '{ingredient_name}', using first one")
                ingredient = Ingredient.objects.filter(name__iexact=ingredient_name).first()
            
            # Calculate total quantity needed (per cake * quantity ordered)
            total_quantity_needed = Decimal(str(ingredient_quantity)) * Decimal(str(quantity))
            
            # Check if we have enough stock
            if ingredient.current_stock < total_quantity_needed:
                print(f"Warning: Insufficient stock for '{ingredient_name}'. "
                      f"Required: {total_quantity_needed}, Available: {ingredient.current_stock}")
                # Still deduct what we have, but log the shortage
                total_quantity_needed = ingredient.current_stock
            
            if total_quantity_needed > 0:
                # Update ingredient stock
                previous_stock = ingredient.current_stock
                new_stock = max(Decimal('0'), previous_stock - total_quantity_needed)
                ingredient.current_stock = new_stock
                ingredient.save()
                
                # Create stock movement record
                StockMovement.objects.create(
                    ingredient=ingredient,
                    movement_type='out',
                    quantity=total_quantity_needed,
                    previous_stock=previous_stock,
                    new_stock=new_stock,
                    unit_cost=ingredient.unit_cost,
                    total_value=total_quantity_needed * ingredient.unit_cost,
                    reference=f"ORDER-{order.order_number}",
                    notes=f"Automatic deduction for order #{order.order_number} - {cake.name} (x{quantity})",
                    created_by=system_user,
                    created_at=timezone.now()
                )
                
                print(f"✅ Deducted {total_quantity_needed} {ingredient_unit} of '{ingredient_name}' "
                      f"for order #{order.order_number}")
    
    except Exception as e:
        print(f"Error deducting ingredients for cake '{cake.name}': {str(e)}")


def create_sample_cake_ingredients():
    """
    Helper function to create sample ingredient data for cakes
    This can be used to set up the ingredients field for existing cakes
    """
    sample_ingredients = {
        'Chocolate Cake': [
            {'name': 'Flour', 'quantity': 0.5, 'unit': 'kg'},
            {'name': 'Sugar', 'quantity': 0.3, 'unit': 'kg'},
            {'name': 'Butter', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Eggs', 'quantity': 3, 'unit': 'pcs'},
            {'name': 'Chocolate Chips', 'quantity': 0.1, 'unit': 'kg'},
        ],
        'Vanilla Cake': [
            {'name': 'Flour', 'quantity': 0.5, 'unit': 'kg'},
            {'name': 'Sugar', 'quantity': 0.3, 'unit': 'kg'},
            {'name': 'Butter', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Eggs', 'quantity': 3, 'unit': 'pcs'},
            {'name': 'Vanilla Extract', 'quantity': 10, 'unit': 'ml'},
        ],
        'Strawberry Cake': [
            {'name': 'Flour', 'quantity': 0.5, 'unit': 'kg'},
            {'name': 'Sugar', 'quantity': 0.3, 'unit': 'kg'},
            {'name': 'Butter', 'quantity': 0.2, 'unit': 'kg'},
            {'name': 'Eggs', 'quantity': 3, 'unit': 'pcs'},
            {'name': 'Strawberries', 'quantity': 0.2, 'unit': 'kg'},
        ]
    }
    
    for cake_name, ingredients in sample_ingredients.items():
        try:
            cake = Cake.objects.get(name__icontains=cake_name)
            cake.ingredients = ingredients
            cake.save()
            print(f"✅ Updated ingredients for '{cake.name}'")
        except Cake.DoesNotExist:
            print(f"Warning: Cake '{cake_name}' not found")
        except Cake.MultipleObjectsReturned:
            print(f"Warning: Multiple cakes found for '{cake_name}'")


if __name__ == '__main__':
    # This can be run to set up sample ingredients for existing cakes
    create_sample_cake_ingredients()
