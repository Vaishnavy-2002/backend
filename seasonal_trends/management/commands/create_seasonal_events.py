from django.core.management.base import BaseCommand
from seasonal_trends.models import SeasonalEvent


class Command(BaseCommand):
    help = 'Create sample seasonal events for the calendar'

    def handle(self, *args, **options):
        """Create sample seasonal events"""
        
        # Clear existing events
        SeasonalEvent.objects.all().delete()
        self.stdout.write('Cleared existing seasonal events')
        
        # Sample seasonal events data
        events_data = [
            # January
            {
                'name': 'New Year Celebration',
                'description': 'Ring in the new year with special celebration cakes',
                'month': 1, 'day': 1, 'year': 2025,
                'sales_level': 'high',
                'products': 'Celebration cakes, Sparkling cakes, Party cakes',
                'expected_revenue': 2500.00,
                'growth_rate': 35.0,
                'icon': 'sparkles',
                'color': 'blue'
            },
            {
                'name': 'Martin Luther King Day',
                'description': 'Honor the legacy with unity-themed cakes',
                'month': 1, 'day': 20, 'year': 2025,
                'sales_level': 'medium',
                'products': 'Unity cakes, Inspirational cakes',
                'expected_revenue': 800.00,
                'growth_rate': 15.0,
                'icon': 'star',
                'color': 'purple'
            },
            
            # February
            {
                'name': 'Valentine\'s Day',
                'description': 'Celebrate love with romantic heart-shaped cakes',
                'month': 2, 'day': 14, 'year': 2025,
                'sales_level': 'peak',
                'products': 'Heart-shaped cakes, Chocolate cakes, Romantic cakes',
                'expected_revenue': 4500.00,
                'growth_rate': 55.0,
                'icon': 'heart',
                'color': 'pink'
            },
            {
                'name': 'Presidents\' Day',
                'description': 'Patriotic themed cakes for the holiday',
                'month': 2, 'day': 17, 'year': 2025,
                'sales_level': 'low',
                'products': 'Patriotic cakes, Red white blue cakes',
                'expected_revenue': 600.00,
                'growth_rate': 8.0,
                'icon': 'star',
                'color': 'blue'
            },
            
            # March
            {
                'name': 'St. Patrick\'s Day',
                'description': 'Green-themed cakes for the Irish celebration',
                'month': 3, 'day': 17, 'year': 2025,
                'sales_level': 'high',
                'products': 'Green cakes, Shamrock cakes, Irish-themed cakes',
                'expected_revenue': 2200.00,
                'growth_rate': 40.0,
                'icon': 'sparkles',
                'color': 'green'
            },
            {
                'name': 'Easter',
                'description': 'Spring celebration with Easter-themed cakes',
                'month': 3, 'day': 31, 'year': 2025,
                'sales_level': 'peak',
                'products': 'Easter cakes, Bunny cakes, Spring cakes, Pastel cakes',
                'expected_revenue': 3800.00,
                'growth_rate': 45.0,
                'icon': 'gift',
                'color': 'yellow'
            },
            
            # April
            {
                'name': 'April Fools\' Day',
                'description': 'Fun and playful cakes for the prankster holiday',
                'month': 4, 'day': 1, 'year': 2025,
                'sales_level': 'medium',
                'products': 'Fun cakes, Prank cakes, Colorful cakes',
                'expected_revenue': 1200.00,
                'growth_rate': 20.0,
                'icon': 'sparkles',
                'color': 'yellow'
            },
            {
                'name': 'Earth Day',
                'description': 'Eco-friendly themed cakes for environmental awareness',
                'month': 4, 'day': 22, 'year': 2025,
                'sales_level': 'low',
                'products': 'Nature cakes, Eco-friendly cakes, Green cakes',
                'expected_revenue': 700.00,
                'growth_rate': 12.0,
                'icon': 'star',
                'color': 'green'
            },
            
            # May
            {
                'name': 'Mother\'s Day',
                'description': 'Celebrate mothers with special floral cakes',
                'month': 5, 'day': 11, 'year': 2025,
                'sales_level': 'peak',
                'products': 'Floral cakes, Elegant cakes, Mother\'s Day specials',
                'expected_revenue': 4200.00,
                'growth_rate': 50.0,
                'icon': 'heart',
                'color': 'pink'
            },
            {
                'name': 'Memorial Day',
                'description': 'Patriotic cakes for remembrance',
                'month': 5, 'day': 26, 'year': 2025,
                'sales_level': 'medium',
                'products': 'Patriotic cakes, Memorial cakes',
                'expected_revenue': 1000.00,
                'growth_rate': 18.0,
                'icon': 'star',
                'color': 'blue'
            },
            
            # June
            {
                'name': 'Father\'s Day',
                'description': 'Celebrate fathers with masculine-themed cakes',
                'month': 6, 'day': 15, 'year': 2025,
                'sales_level': 'high',
                'products': 'Masculine cakes, Sports cakes, BBQ-themed cakes',
                'expected_revenue': 2800.00,
                'growth_rate': 35.0,
                'icon': 'gift',
                'color': 'blue'
            },
            {
                'name': 'Summer Solstice',
                'description': 'Welcome summer with bright, sunny cakes',
                'month': 6, 'day': 21, 'year': 2025,
                'sales_level': 'medium',
                'products': 'Summer cakes, Bright cakes, Tropical cakes',
                'expected_revenue': 1500.00,
                'growth_rate': 25.0,
                'icon': 'sparkles',
                'color': 'yellow'
            },
            
            # July
            {
                'name': 'Independence Day',
                'description': 'Patriotic cakes for the 4th of July',
                'month': 7, 'day': 4, 'year': 2025,
                'sales_level': 'peak',
                'products': 'Patriotic cakes, Red white blue cakes, Firework cakes',
                'expected_revenue': 3600.00,
                'growth_rate': 48.0,
                'icon': 'fire',
                'color': 'red'
            },
            {
                'name': 'Bastille Day',
                'description': 'French-themed cakes for the celebration',
                'month': 7, 'day': 14, 'year': 2025,
                'sales_level': 'low',
                'products': 'French cakes, Elegant cakes',
                'expected_revenue': 500.00,
                'growth_rate': 10.0,
                'icon': 'star',
                'color': 'blue'
            },
            
            # August
            {
                'name': 'Back to School',
                'description': 'Celebrate the new school year with fun cakes',
                'month': 8, 'day': 15, 'year': 2025,
                'sales_level': 'medium',
                'products': 'School-themed cakes, Fun cakes, Educational cakes',
                'expected_revenue': 1800.00,
                'growth_rate': 28.0,
                'icon': 'gift',
                'color': 'yellow'
            },
            {
                'name': 'National Ice Cream Day',
                'description': 'Ice cream themed cakes for the sweet holiday',
                'month': 8, 'day': 18, 'year': 2025,
                'sales_level': 'high',
                'products': 'Ice cream cakes, Frozen cakes, Sweet cakes',
                'expected_revenue': 2400.00,
                'growth_rate': 38.0,
                'icon': 'sparkles',
                'color': 'pink'
            },
            
            # September
            {
                'name': 'Labor Day',
                'description': 'Celebrate workers with appreciation cakes',
                'month': 9, 'day': 1, 'year': 2025,
                'sales_level': 'medium',
                'products': 'Worker appreciation cakes, Celebration cakes',
                'expected_revenue': 1300.00,
                'growth_rate': 22.0,
                'icon': 'star',
                'color': 'blue'
            },
            {
                'name': 'Autumn Equinox',
                'description': 'Welcome fall with autumn-themed cakes',
                'month': 9, 'day': 22, 'year': 2025,
                'sales_level': 'medium',
                'products': 'Autumn cakes, Fall cakes, Harvest cakes',
                'expected_revenue': 1600.00,
                'growth_rate': 30.0,
                'icon': 'gift',
                'color': 'orange'
            },
            
            # October
            {
                'name': 'Halloween',
                'description': 'Spooky and fun Halloween-themed cakes',
                'month': 10, 'day': 31, 'year': 2025,
                'sales_level': 'peak',
                'products': 'Halloween cakes, Spooky cakes, Pumpkin cakes, Monster cakes',
                'expected_revenue': 4800.00,
                'growth_rate': 60.0,
                'icon': 'fire',
                'color': 'orange'
            },
            {
                'name': 'Mid-Autumn Festival',
                'description': 'Traditional autumn celebration cakes',
                'month': 10, 'day': 15, 'year': 2025,
                'sales_level': 'medium',
                'products': 'Autumn cakes, Traditional cakes, Moon cakes',
                'expected_revenue': 1400.00,
                'growth_rate': 25.0,
                'icon': 'calendar',
                'color': 'yellow'
            },
            
            # November
            {
                'name': 'Thanksgiving',
                'description': 'Grateful celebration with harvest-themed cakes',
                'month': 11, 'day': 27, 'year': 2025,
                'sales_level': 'peak',
                'products': 'Thanksgiving cakes, Harvest cakes, Gratitude cakes',
                'expected_revenue': 4100.00,
                'growth_rate': 52.0,
                'icon': 'gift',
                'color': 'orange'
            },
            {
                'name': 'Black Friday',
                'description': 'Shopping celebration with discount-themed cakes',
                'month': 11, 'day': 28, 'year': 2025,
                'sales_level': 'high',
                'products': 'Sale cakes, Discount cakes, Shopping cakes',
                'expected_revenue': 2600.00,
                'growth_rate': 40.0,
                'icon': 'sparkles',
                'color': 'red'
            },
            
            # December
            {
                'name': 'Christmas',
                'description': 'Festive Christmas celebration cakes',
                'month': 12, 'day': 25, 'year': 2025,
                'sales_level': 'peak',
                'products': 'Christmas cakes, Holiday cakes, Festive cakes, Santa cakes',
                'expected_revenue': 5500.00,
                'growth_rate': 65.0,
                'icon': 'gift',
                'color': 'red'
            },
            {
                'name': 'New Year\'s Eve',
                'description': 'Ring in the new year with celebration cakes',
                'month': 12, 'day': 31, 'year': 2025,
                'sales_level': 'high',
                'products': 'New Year cakes, Celebration cakes, Sparkling cakes',
                'expected_revenue': 3200.00,
                'growth_rate': 45.0,
                'icon': 'sparkles',
                'color': 'blue'
            }
        ]
        
        # Create events
        created_count = 0
        for event_data in events_data:
            event, created = SeasonalEvent.objects.get_or_create(
                name=event_data['name'],
                month=event_data['month'],
                day=event_data['day'],
                year=event_data['year'],
                defaults=event_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} seasonal events'
            )
        )
        
        # Display summary
        total_events = SeasonalEvent.objects.count()
        total_revenue = sum(event.expected_revenue for event in SeasonalEvent.objects.all())
        
        self.stdout.write(f'Total events in database: {total_events}')
        self.stdout.write(f'Total expected revenue: Rs {total_revenue:,.2f}')
        
        # Show events by month
        self.stdout.write('\nEvents by month:')
        for month in range(1, 13):
            month_events = SeasonalEvent.objects.filter(month=month)
            if month_events.exists():
                month_name = month_events.first().get_month_name()
                count = month_events.count()
                revenue = sum(event.expected_revenue for event in month_events)
                self.stdout.write(f'  {month_name}: {count} events, Rs {revenue:,.2f}')
