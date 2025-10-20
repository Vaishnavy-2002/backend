#!/usr/bin/env python3
"""
Utility script to add real orders to the database for analytics testing
Run this script when you want to add actual orders for testing analytics
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sweetbite_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from orders.models import Order, OrderItem, ShippingAddress
from cakes.models import Cake
from users.models import User

def create_real_order(customer, cakes, order_date=None):
    """Create a single real order"""
    if not order_date:
        order_date = timezone.now()
    
    # Create shipping address for the customer
    shipping_address, created = ShippingAddress.objects.get_or_create(
        customer=customer,
        defaults={
            'first_name': customer.first_name or 'Customer',
            'last_name': customer.last_name or 'Name',
            'phone': '+1234567890',
            'address_line1': '123 Main Street',
            'city': 'Your City',
            'state': 'Your State',
            'postal_code': '12345',
            'country': 'Your Country',
            'is_default': True
        }
    )
    
    # Create order
    order = Order.objects.create(
        customer=customer,
        order_type='online',
        order_status='delivered',
        payment_status='paid',
        payment_method='card',
        shipping_address=shipping_address,
        subtotal=Decimal('0.00'),
        tax=Decimal('0.00'),
        delivery_fee=Decimal('0.00'),
        total_amount=Decimal('0.00'),
        created_at=order_date,
        delivered_at=order_date + timedelta(hours=random.randint(1, 24))
    )
    
    # Add random cakes to the order
    num_items = random.randint(1, 3)
    selected_cakes = random.sample(cakes, min(num_items, len(cakes)))
    
    order_subtotal = Decimal('0.00')
    
    for cake in selected_cakes:
        quantity = random.randint(1, 2)
        unit_price = cake.price
        total_price = unit_price * quantity
        
        OrderItem.objects.create(
            order=order,
            cake=cake,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        
        order_subtotal += total_price
    
    # Update order totals
    tax = order_subtotal * Decimal('0.08')  # 8% tax
    delivery_fee = Decimal('5.00') if order_subtotal < Decimal('50.00') else Decimal('0.00')
    total_amount = order_subtotal + tax + delivery_fee
    
    order.subtotal = order_subtotal
    order.tax = tax
    order.delivery_fee = delivery_fee
    order.total_amount = total_amount
    order.save()
    
    return order

def add_sample_orders():
    """Add some sample orders for testing analytics"""
    
    print("🍰 Adding sample orders for analytics testing...")
    
    # Get or create a customer
    customer, created = User.objects.get_or_create(
        username='demo_customer',
        defaults={
            'email': 'demo@customer.com',
            'first_name': 'Demo',
            'last_name': 'Customer',
            'user_type': 'customer',
            'is_active': True
        }
    )
    
    if created:
        customer.set_password('demopass123')
        customer.save()
        print(f"Created demo customer: {customer.username}")
    else:
        print(f"Using existing demo customer: {customer.username}")
    
    # Get all cakes
    cakes = list(Cake.objects.all())
    if not cakes:
        print("❌ No cakes found! Please create cakes first.")
        return
    
    print(f"Found {len(cakes)} cakes")
    
    # Create sample orders for the last 30 days
    orders_created = 0
    
    for i in range(20):  # Create 20 sample orders
        # Random date within last 30 days
        days_ago = random.randint(0, 30)
        order_date = timezone.now() - timedelta(days=days_ago)
        
        order = create_real_order(customer, cakes, order_date)
        orders_created += 1
    
    print(f"✅ Created {orders_created} sample orders")
    
    # Print summary
    total_orders = Order.objects.count()
    delivered_orders = Order.objects.filter(order_status='delivered').count()
    total_revenue = Order.objects.filter(order_status='delivered').aggregate(
        total=models.Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    print(f"\n📊 Analytics Summary:")
    print(f"Total Orders: {total_orders}")
    print(f"Delivered Orders: {delivered_orders}")
    print(f"Total Revenue: Rs {total_revenue:,.2f}")
    
    print("\n✨ Sample orders added successfully!")
    print("You can now view real analytics data in the Best-Selling Items & Profit Analyzer.")

if __name__ == '__main__':
    from django.db import models
    add_sample_orders()
