from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models
from feedback.models import Feedback
from orders.models import Order
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Add sample feedback data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Adding sample feedback data...')

        # Sample feedback messages
        positive_feedback = [
            "Absolutely delicious! The cake was fresh and beautifully decorated.",
            "Amazing taste and perfect presentation. Will definitely order again!",
            "The chocolate cake was heavenly. Best bakery in town!",
            "Outstanding quality and service. Highly recommended!",
            "Perfect for our celebration. Everyone loved it!",
            "The flavors were incredible and the design was exactly what we wanted.",
            "Fresh ingredients and excellent craftsmanship. 5 stars!",
            "Exceeded our expectations. The cake was a hit at the party!",
            "Beautiful decoration and amazing taste. Worth every penny!",
            "Professional service and delicious results. Thank you!"
        ]

        neutral_feedback = [
            "Good cake, but delivery was a bit late.",
            "The taste was nice, but expected a bit more for the price.",
            "Decent quality, might try different flavors next time.",
            "Satisfactory experience overall. Room for improvement.",
            "The cake was okay, nothing extraordinary but acceptable."
        ]

        negative_feedback = [
            "The cake was too sweet for our liking.",
            "Delivery was delayed and the cake arrived damaged.",
            "Not as fresh as expected. Disappointed with the quality."
        ]

        # Get or create sample users
        users = []
        sample_usernames = ['alice_johnson', 'bob_smith', 'carol_brown', 'david_wilson', 'emma_davis']
        
        for username in sample_usernames:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': username.split('_')[0].title(),
                    'last_name': username.split('_')[1].title(),
                    'user_type': 'customer'
                }
            )
            users.append(user)
            if created:
                self.stdout.write(f'Created user: {username}')

        # Clear existing feedback
        Feedback.objects.all().delete()
        self.stdout.write('Cleared existing feedback data')

        # Create sample feedback
        feedback_count = 0
        
        # Add positive feedback (rating 4-5)
        for _ in range(12):
            feedback = Feedback.objects.create(
                user=random.choice(users),
                message=random.choice(positive_feedback),
                rating=random.choice([4, 5, 5, 5])  # More 5-star ratings
            )
            feedback_count += 1

        # Add neutral feedback (rating 3)
        for _ in range(4):
            feedback = Feedback.objects.create(
                user=random.choice(users),
                message=random.choice(neutral_feedback),
                rating=3
            )
            feedback_count += 1

        # Add some 4-star feedback
        for _ in range(3):
            feedback = Feedback.objects.create(
                user=random.choice(users),
                message=random.choice(positive_feedback),
                rating=4
            )
            feedback_count += 1

        # Add a couple of negative feedback (rating 1-2)
        for _ in range(2):
            feedback = Feedback.objects.create(
                user=random.choice(users),
                message=random.choice(negative_feedback),
                rating=random.choice([1, 2])
            )
            feedback_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully added {feedback_count} sample feedback entries!')
        )
        
        # Show statistics
        total_feedback = Feedback.objects.count()
        avg_rating = Feedback.objects.aggregate(
            avg_rating=models.Avg('rating')
        )['avg_rating'] or 0
        
        self.stdout.write(f'Total feedback: {total_feedback}')
        self.stdout.write(f'Average rating: {avg_rating:.2f}')
        
        # Rating distribution
        for rating in range(1, 6):
            count = Feedback.objects.filter(rating=rating).count()
            self.stdout.write(f'{rating} stars: {count} reviews')
