from django.core.management.base import BaseCommand
from django.db import transaction
from feedback.models import Feedback, TestimonialSettings


class Command(BaseCommand):
    help = 'Setup enhanced feedback system with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate-data',
            action='store_true',
            help='Migrate existing feedback data to new format',
        )
        parser.add_argument(
            '--create-settings',
            action='store_true',
            help='Create initial testimonial settings',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up enhanced feedback system...')
        )

        if options['migrate_data']:
            self.migrate_existing_data()

        if options['create_settings']:
            self.create_initial_settings()

        self.stdout.write(
            self.style.SUCCESS('Enhanced feedback system setup complete!')
        )

    @transaction.atomic
    def migrate_existing_data(self):
        """Migrate existing feedback data to new format"""
        self.stdout.write('Migrating existing feedback data...')
        
        feedbacks_updated = 0
        
        for feedback in Feedback.objects.all():
            updated = False
            
            # Copy message to comment if comment is empty
            if not feedback.comment and feedback.message:
                feedback.comment = feedback.message
                updated = True
            
            # Auto-feature high ratings
            if feedback.rating >= 5 and not feedback.is_featured:
                feedback.is_featured = True
                updated = True
                
            # Mark as verified if user exists
            if feedback.user and not feedback.is_verified:
                feedback.is_verified = True
                updated = True
            
            if updated:
                feedback.save()
                feedbacks_updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Updated {feedbacks_updated} existing feedback records')
        )

    def create_initial_settings(self):
        """Create initial testimonial settings"""
        self.stdout.write('Creating initial testimonial settings...')
        
        settings, created = TestimonialSettings.objects.get_or_create(
            defaults={
                'max_testimonials_homepage': 3,
                'require_images_for_homepage': False,
                'auto_feature_high_ratings': True,
                'min_rating_for_homepage': 4
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created initial testimonial settings')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Testimonial settings already exist')
            )

    def update_featured_status(self):
        """Update featured status based on ratings"""
        self.stdout.write('Updating featured status...')
        
        # Auto-feature 5-star reviews
        count = Feedback.objects.filter(
            rating=5,
            is_featured=False
        ).update(is_featured=True)
        
        self.stdout.write(
            self.style.SUCCESS(f'Featured {count} high-rating feedback items')
        )
