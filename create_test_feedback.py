#!/usr/bin/env python
"""
Create test data for feedback edit/delete functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sweetbite_backend.settings')
django.setup()

from users.models import User
from orders.models import Order, OrderItem, ShippingAddress
from cakes.models import Cake, Category
from feedback.models import Feedback
from django.contrib.auth import authenticate

def create_test_data():
    """Create test user, order, and feedback"""
    print("🧪 Creating Test Data for Feedback Edit/Delete")
    print("=" * 60)
    
    # Step 1: Create or get test user
    try:
        user, created = User.objects.get_or_create(
            username='feedback_test_user',
            defaults={
                'email': 'feedback_test@example.com',
                'password': 'testpass123',
                'first_name': 'Feedback',
                'last_name': 'Test'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username}")
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None
    
    # Step 2: Create or get test cake
    try:
        # Get or create category first
        category, _ = Category.objects.get_or_create(
            name='Birthday',
            defaults={'description': 'Birthday cakes'}
        )
        
        cake, created = Cake.objects.get_or_create(
            name='Test Cake for Feedback',
            defaults={
                'description': 'A test cake for feedback functionality',
                'price': 25.00,
                'category': category,
                'image': 'https://example.com/cake.jpg',
                'is_available': True
            }
        )
        if created:
            print(f"✅ Created test cake: {cake.name}")
        else:
            print(f"✅ Using existing test cake: {cake.name}")
    except Exception as e:
        print(f"❌ Error creating test cake: {e}")
        return None
    
    # Step 3: Create shipping address
    try:
        address, created = ShippingAddress.objects.get_or_create(
            customer=user,
            first_name='Test',
            last_name='User',
            defaults={
                'phone': '+1234567890',
                'address_line1': '123 Test Street',
                'city': 'Test City',
                'state': 'Test State',
                'postal_code': '12345',
                'is_default': True
            }
        )
        if created:
            print(f"✅ Created shipping address")
        else:
            print(f"✅ Using existing shipping address")
    except Exception as e:
        print(f"❌ Error creating shipping address: {e}")
        return None
    
    # Step 4: Create test order
    try:
        # Check if order already exists
        existing_order = Order.objects.filter(customer=user, order_status='delivered').first()
        
        if existing_order:
            print(f"✅ Using existing delivered order: {existing_order.order_number}")
            order = existing_order
        else:
            order = Order.objects.create(
                customer=user,
                order_type='online',
                shipping_address=address,
                delivery_instructions='Test order for feedback',
                subtotal=25.00,
                tax=2.50,
                delivery_fee=5.00,
                total_amount=32.50,
                order_status='delivered',  # Set to delivered so feedback is available
                payment_status='pending'
            )
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                cake=cake,
                quantity=1,
                unit_price=25.00,
                total_price=25.00,
                customization_notes='Test order item'
            )
            
            print(f"✅ Created test order: {order.order_number}")
    except Exception as e:
        print(f"❌ Error creating test order: {e}")
        return None
    
    # Step 5: Create test feedback
    try:
        existing_feedback = Feedback.objects.filter(user=user, order=order).first()
        
        if existing_feedback:
            print(f"✅ Using existing feedback: {existing_feedback.rating} stars")
            feedback = existing_feedback
        else:
            feedback = Feedback.objects.create(
                user=user,
                order=order,
                message='This is a test feedback message. The service was excellent and the cake was delicious! I would definitely order again.',
                rating=5
            )
            print(f"✅ Created test feedback: {feedback.rating} stars")
    except Exception as e:
        print(f"❌ Error creating test feedback: {e}")
        return None
    
    # Step 6: Print access information
    print("\n" + "=" * 60)
    print("🎯 TEST DATA READY!")
    print("=" * 60)
    print(f"👤 Test User: {user.username}")
    print(f"🔑 Password: testpass123")
    print(f"📦 Order ID: {order.id}")
    print(f"📦 Order Number: {order.order_number}")
    print(f"⭐ Feedback ID: {feedback.id}")
    print(f"⭐ Feedback Rating: {feedback.rating} stars")
    print("\n🌐 HOW TO ACCESS EDIT/DELETE OPTIONS:")
    print("1. Login with: feedback_test_user / testpass123")
    print("2. Go to: /orders (MyOrdersPage)")
    print("3. Click 'View Full Order' for the delivered order")
    print("4. Look in the right sidebar for 'Your Feedback' section")
    print("5. You'll see [Edit Feedback] and [Delete] buttons!")
    print("\n🔗 Direct URL:")
    print(f"   /order-confirmation/{order.id}")
    print("=" * 60)
    
    return {
        'user': user,
        'order': order,
        'feedback': feedback
    }

if __name__ == '__main__':
    create_test_data()
