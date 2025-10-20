from django.db import models
from django.contrib.auth import get_user_model
from cakes.models import Cake

User = get_user_model()

class ShippingAddress(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='', blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shipping_addresses'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.city}, {self.state}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Set other addresses to non-default
            ShippingAddress.objects.filter(customer=self.customer, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD = [
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('cash', 'Cash on Delivery'),
    ]
    
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_date = models.DateTimeField(blank=True, null=True)
    failure_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
    
    def __str__(self):
        return f"Payment for Order #{self.order.order_number} - {self.payment_status}"

class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup/Delivery'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('online', 'Online Payment'),
    ]
    
    ORDER_TYPE = [
        ('online', 'Online Order'),
        ('walk_in', 'Walk-in Order'),
    ]
    
    # Order Details
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE, default='online')
    
    # Guest order fields
    is_guest_order = models.BooleanField(default=False)
    guest_email = models.EmailField(blank=True, null=True)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Status
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD, default='cash')
    
    # Delivery Details
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    delivery_address = models.TextField(blank=True, null=True)  # Keep for backward compatibility
    delivery_instructions = models.TextField(blank=True, null=True)
    delivery_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    delivery_date = models.DateField(blank=True, null=True)
    delivery_time = models.TimeField(blank=True, null=True)
    
    # Location Tracking
    delivery_latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    delivery_longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    current_latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    current_longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    tracking_enabled = models.BooleanField(default=False)
    
    # Financial
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    # Staff assigned
    assigned_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import datetime
            today = datetime.datetime.now()
            last_order = Order.objects.filter(created_at__date=today.date()).order_by('-id').first()
            if last_order:
                last_number = int(last_order.order_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.order_number = f"SB{today.strftime('%Y%m%d')}{new_number:04d}"
        
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    cake = models.ForeignKey(Cake, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    customization_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'order_items'
    
    def __str__(self):
        return f"{self.quantity}x {self.cake.name} - Order #{self.order.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS)
    notes = models.TextField(blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_status_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order.order_number} - {self.status}"

class DeliveryLocationHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='location_history')
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    accuracy = models.FloatField(blank=True, null=True)  # GPS accuracy in meters
    speed = models.FloatField(blank=True, null=True)  # Speed in km/h
    heading = models.FloatField(blank=True, null=True)  # Direction in degrees
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'delivery_location_history'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Order #{self.order.order_number} - {self.latitude}, {self.longitude}"
