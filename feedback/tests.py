from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Feedback

User = get_user_model()


class FeedbackModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_feedback_creation(self):
        feedback = Feedback.objects.create(
            user=self.user,
            message='Great service!',
            rating=5
        )
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.message, 'Great service!')
        self.assertEqual(feedback.rating, 5)
        self.assertIsNotNone(feedback.created_at)

    def test_anonymous_feedback(self):
        feedback = Feedback.objects.create(
            user=None,
            message='Good experience',
            rating=4
        )
        self.assertIsNone(feedback.user)
        self.assertEqual(feedback.message, 'Good experience')
        self.assertEqual(feedback.rating, 4)


class FeedbackAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.feedback_data = {
            'message': 'Excellent service and delicious cakes!',
            'rating': 5
        }

    def test_create_feedback_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('feedback-list')
        response = self.client.post(url, self.feedback_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 1)
        self.assertEqual(Feedback.objects.first().user, self.user)

    def test_create_feedback_anonymous(self):
        url = reverse('feedback-list')
        response = self.client.post(url, self.feedback_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 1)
        self.assertIsNone(Feedback.objects.first().user)

    def test_feedback_validation(self):
        url = reverse('feedback-list')
        invalid_data = {
            'message': 'Short',  # Less than 10 characters
            'rating': 6  # Invalid rating
        }
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_feedback_stats(self):
        # Create some test feedback
        Feedback.objects.create(user=self.user, message='Great!', rating=5)
        Feedback.objects.create(user=None, message='Good service', rating=4)
        Feedback.objects.create(user=self.user, message='Average', rating=3)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('feedback-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_feedback'], 3)
        self.assertEqual(response.data['average_rating'], 4.0)
