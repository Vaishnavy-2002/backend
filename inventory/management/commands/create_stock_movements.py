from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import Ingredient, StockMovement
from decimal import Decimal
import random
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample stock movements for testing inventory reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of stock movements to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing stock movements before creating new ones'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days back to create movements (default: 30)'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear_existing = options['clear']
        days_back = options['days']

        # Get or create a user
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@sweetbite.com',
                'is_staff': True,
                'is_superuser': True
            }
        )

        # Get all ingredients
        ingredients = Ingredient.objects.all()

        if not ingredients.exists():
            self.stdout.write(
                self.style.ERROR('No ingredients found. Please create some ingredients first.')
            )
            return

        self.stdout.write(f'Found {ingredients.count()} ingredients')

        # Clear existing stock movements if requested
        if clear_existing:
            deleted_count = StockMovement.objects.count()
            StockMovement.objects.all().delete()
            self.stdout.write(f'Cleared {deleted_count} existing stock movements')

        # Create sample movements
        movement_types = ['in', 'out', 'adjustment', 'waste']
        base_date = datetime.now() - timedelta(days=days_back)

        movements_created = 0

        for i in range(count):
            ingredient = random.choice(ingredients)
            movement_type = random.choice(movement_types)

            # Random quantity between 1 and 50
            quantity = Decimal(str(round(random.uniform(1, 50), 3)))

            # Random unit cost between 1 and 20
            unit_cost = Decimal(str(round(random.uniform(1, 20), 2)))

            # Calculate previous and new stock
            previous_stock = ingredient.current_stock

            if movement_type == 'in':
                new_stock = previous_stock + quantity
            elif movement_type == 'out':
                new_stock = max(Decimal('0'), previous_stock - quantity)
            elif movement_type == 'adjustment':
                new_stock = quantity
            elif movement_type == 'waste':
                new_stock = max(Decimal('0'), previous_stock - quantity)

            # Update ingredient stock
            ingredient.current_stock = new_stock
            ingredient.save()

            # Calculate total value
            total_value = quantity * unit_cost

            # Random date within the specified days back
            random_days = random.randint(0, days_back)
            created_at = base_date + timedelta(days=random_days)

            # Create the movement
            movement = StockMovement.objects.create(
                ingredient=ingredient,
                movement_type=movement_type,
                quantity=quantity,
                previous_stock=previous_stock,
                new_stock=new_stock,
                unit_cost=unit_cost,
                total_value=total_value,
                reference=f"REF-{random.randint(1000, 9999)}",
                notes=f"Sample {movement_type} movement",
                created_by=user,
                created_at=created_at
            )

            movements_created += 1

            if movements_created % 10 == 0:
                self.stdout.write(f'Created {movements_created} movements...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {movements_created} sample stock movements')
        )

        # Print summary
        total_movements = StockMovement.objects.count()
        total_value = sum(m.total_value for m in StockMovement.objects.all())

        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'Total movements: {total_movements}')
        self.stdout.write(f'Total value: RS {total_value:.2f}')

        # Print by type
        self.stdout.write(f'\nBy movement type:')
        for movement_type in movement_types:
            count_by_type = StockMovement.objects.filter(movement_type=movement_type).count()
            self.stdout.write(f'  {movement_type}: {count_by_type} movements')

        # Print by ingredient
        self.stdout.write(f'\nBy ingredient:')
        for ingredient in ingredients:
            count_by_ingredient = StockMovement.objects.filter(ingredient=ingredient).count()
            if count_by_ingredient > 0:
                self.stdout.write(f'  {ingredient.name}: {count_by_ingredient} movements')
