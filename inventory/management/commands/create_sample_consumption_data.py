from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import Ingredient, StockMovement
from decimal import Decimal
import random
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample consumption data for ingredient analysis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing stock movements before creating new ones.',
        )

    def handle(self, *args, **kwargs):
        if kwargs['clear']:
            StockMovement.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing stock movements'))

        # Get or create sample ingredients
        ingredients_data = [
            {'name': 'All-Purpose Flour', 'unit': 'kg', 'current_stock': 25.0, 'unit_cost': 2.50},
            {'name': 'Granulated Sugar', 'unit': 'kg', 'current_stock': 18.5, 'unit_cost': 3.20},
            {'name': 'Chocolate Chips', 'unit': 'kg', 'current_stock': 8.2, 'unit_cost': 8.50},
            {'name': 'Butter', 'unit': 'kg', 'current_stock': 5.5, 'unit_cost': 6.80},
            {'name': 'Eggs', 'unit': 'pcs', 'current_stock': 120, 'unit_cost': 0.25},
            {'name': 'Vanilla Extract', 'unit': 'ml', 'current_stock': 500, 'unit_cost': 0.15},
            {'name': 'Baking Powder', 'unit': 'g', 'current_stock': 200, 'unit_cost': 0.05},
            {'name': 'Coconut Flakes', 'unit': 'kg', 'current_stock': 2.1, 'unit_cost': 4.20},
            {'name': 'Almond Extract', 'unit': 'ml', 'current_stock': 150, 'unit_cost': 0.20},
            {'name': 'Pecans', 'unit': 'kg', 'current_stock': 1.8, 'unit_cost': 12.00},
        ]

        ingredients = []
        for ing_data in ingredients_data:
            ingredient, created = Ingredient.objects.get_or_create(
                name=ing_data['name'],
                defaults={
                    'unit': ing_data['unit'],
                    'current_stock': Decimal(str(ing_data['current_stock'])),
                    'unit_cost': Decimal(str(ing_data['unit_cost'])),
                    'minimum_stock': Decimal(str(ing_data['current_stock'] * 0.2)),  # 20% of current stock
                    'is_active': True
                }
            )
            ingredients.append(ingredient)
            if created:
                self.stdout.write(f'Created ingredient: {ingredient.name}')

        # Get admin user for created_by
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.first()

        # Create sample stock movements for the last 30 days
        movements_created = 0
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        for i in range(100):  # Create 100 random movements
            ingredient = random.choice(ingredients)
            movement_date = start_date + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Determine movement type (70% outbound, 20% waste, 10% inbound)
            movement_type = random.choices(
                ['out', 'waste', 'in'],
                weights=[70, 20, 10]
            )[0]
            
            # Generate realistic quantities
            if movement_type == 'out':
                quantity = Decimal(str(random.uniform(0.1, 2.0)))
            elif movement_type == 'waste':
                quantity = Decimal(str(random.uniform(0.05, 0.5)))
            else:  # in
                quantity = Decimal(str(random.uniform(1.0, 10.0)))
            
            # Calculate stock changes
            previous_stock = ingredient.current_stock
            if movement_type == 'in':
                new_stock = previous_stock + quantity
            else:
                new_stock = max(Decimal('0'), previous_stock - quantity)
            
            total_value = quantity * ingredient.unit_cost
            
            movement = StockMovement.objects.create(
                ingredient=ingredient,
                movement_type=movement_type,
                quantity=quantity,
                previous_stock=previous_stock,
                new_stock=new_stock,
                unit_cost=ingredient.unit_cost,
                total_value=total_value,
                reference=f"Sample-{i+1:03d}",
                notes=f"Sample {movement_type} movement",
                created_by=admin_user,
                created_at=movement_date
            )
            
            # Update ingredient current stock
            ingredient.current_stock = new_stock
            ingredient.save()
            
            movements_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {movements_created} sample stock movements'
            )
        )
        
        # Show summary
        total_movements = StockMovement.objects.count()
        outbound_movements = StockMovement.objects.filter(movement_type='out').count()
        waste_movements = StockMovement.objects.filter(movement_type='waste').count()
        inbound_movements = StockMovement.objects.filter(movement_type='in').count()
        
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'Total movements: {total_movements}')
        self.stdout.write(f'Outbound (consumption): {outbound_movements}')
        self.stdout.write(f'Waste: {waste_movements}')
        self.stdout.write(f'Inbound (restock): {inbound_movements}')
        
        # Show top consumed ingredients
        from django.db.models import Sum
        top_consumed = StockMovement.objects.filter(
            movement_type__in=['out', 'waste']
        ).values('ingredient__name').annotate(
            total_consumed=Sum('quantity')
        ).order_by('-total_consumed')[:5]
        
        self.stdout.write(f'\nTop 5 consumed ingredients:')
        for item in top_consumed:
            self.stdout.write(f'  {item["ingredient__name"]}: {item["total_consumed"]} units')
