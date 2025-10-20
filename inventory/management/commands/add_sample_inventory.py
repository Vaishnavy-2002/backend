from django.core.management.base import BaseCommand
from inventory.models import Category, Supplier

class Command(BaseCommand):
    help = 'Add sample categories and suppliers for inventory management'

    def handle(self, *args, **options):
        self.stdout.write('Adding sample inventory data...')

        # Clear existing data
        Category.objects.all().delete()
        Supplier.objects.all().delete()
        self.stdout.write('Cleared existing categories and suppliers')

        # Sample categories for bakery ingredients
        categories_data = [
            {
                'name': 'Flour & Grains',
                'description': 'Different types of flour and grain-based ingredients'
            },
            {
                'name': 'Sugar & Sweeteners',
                'description': 'Various types of sugar and sweetening agents'
            },
            {
                'name': 'Dairy Products',
                'description': 'Milk, butter, cream, cheese and other dairy items'
            },
            {
                'name': 'Eggs & Proteins',
                'description': 'Eggs and protein-based ingredients'
            },
            {
                'name': 'Fats & Oils',
                'description': 'Cooking oils, butter, margarine and other fats'
            },
            {
                'name': 'Leavening Agents',
                'description': 'Baking powder, baking soda, yeast and rising agents'
            },
            {
                'name': 'Flavorings & Extracts',
                'description': 'Vanilla, almond extract, food coloring, essences'
            },
            {
                'name': 'Chocolate & Cocoa',
                'description': 'Chocolate chips, cocoa powder, chocolate bars'
            },
            {
                'name': 'Fruits & Nuts',
                'description': 'Fresh fruits, dried fruits, nuts and seeds'
            },
            {
                'name': 'Spices & Seasonings',
                'description': 'Cinnamon, salt, pepper and other spices'
            },
            {
                'name': 'Decorating Supplies',
                'description': 'Sprinkles, fondant, icing sugar, food coloring'
            },
            {
                'name': 'Packaging Materials',
                'description': 'Boxes, bags, containers and packaging supplies'
            }
        ]

        # Sample suppliers
        suppliers_data = [
            {
                'name': 'Premium Flour Mills',
                'contact_person': 'John Smith',
                'email': 'orders@premiumflour.com',
                'phone': '+1-555-0101',
                'address': '123 Mill Street, Flour City, FC 12345',
                'website': 'https://premiumflour.com',
                'notes': 'High quality flour supplier, reliable delivery'
            },
            {
                'name': 'Sweet Valley Dairy',
                'contact_person': 'Sarah Johnson',
                'email': 'sales@sweetvalleydairy.com',
                'phone': '+1-555-0102',
                'address': '456 Dairy Lane, Milktown, MT 67890',
                'website': 'https://sweetvalleydairy.com',
                'notes': 'Fresh dairy products, same-day delivery available'
            },
            {
                'name': 'Golden Eggs Farm',
                'contact_person': 'Mike Brown',
                'email': 'info@goldeneggsfarm.com',
                'phone': '+1-555-0103',
                'address': '789 Farm Road, Eggville, EV 11111',
                'notes': 'Farm-fresh eggs, organic options available'
            },
            {
                'name': 'Chocolate Dreams Inc.',
                'contact_person': 'Lisa Davis',
                'email': 'wholesale@chocolatedreams.com',
                'phone': '+1-555-0104',
                'address': '321 Cocoa Boulevard, Choctown, CT 22222',
                'website': 'https://chocolatedreams.com',
                'notes': 'Premium chocolate supplier, bulk discounts available'
            },
            {
                'name': 'Spice & Everything Nice',
                'contact_person': 'Ahmed Hassan',
                'email': 'orders@spicenice.com',
                'phone': '+1-555-0105',
                'address': '654 Spice Market, Flavortown, FT 33333',
                'notes': 'Wide variety of spices and flavorings'
            },
            {
                'name': 'Fresh Fruit Distributors',
                'contact_person': 'Maria Garcia',
                'email': 'sales@freshfruitdist.com',
                'phone': '+1-555-0106',
                'address': '987 Orchard Avenue, Fruitdale, FD 44444',
                'notes': 'Seasonal fruits and nuts, competitive pricing'
            },
            {
                'name': 'Baker\'s Supply Co.',
                'contact_person': 'Robert Wilson',
                'email': 'info@bakerssupply.com',
                'phone': '+1-555-0107',
                'address': '147 Baker Street, Pastryville, PV 55555',
                'website': 'https://bakerssupply.com',
                'notes': 'One-stop shop for all baking supplies and equipment'
            },
            {
                'name': 'Packaging Plus',
                'contact_person': 'Jennifer Lee',
                'email': 'sales@packagingplus.com',
                'phone': '+1-555-0108',
                'address': '258 Package Lane, Boxburg, BB 66666',
                'notes': 'Custom packaging solutions, eco-friendly options'
            }
        ]

        # Create categories
        category_count = 0
        for cat_data in categories_data:
            category = Category.objects.create(**cat_data)
            category_count += 1
            self.stdout.write(f'Created category: {category.name}')

        # Create suppliers
        supplier_count = 0
        for sup_data in suppliers_data:
            supplier = Supplier.objects.create(**sup_data)
            supplier_count += 1
            self.stdout.write(f'Created supplier: {supplier.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {category_count} categories and {supplier_count} suppliers!'
            )
        )
        
        self.stdout.write('\nCategories created:')
        for category in Category.objects.all():
            self.stdout.write(f'  - {category.name}')
            
        self.stdout.write('\nSuppliers created:')
        for supplier in Supplier.objects.all():
            self.stdout.write(f'  - {supplier.name}')




