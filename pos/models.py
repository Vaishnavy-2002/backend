from django.db import models
from django.contrib.auth import get_user_model
from cakes.models import Cake
from orders.models import Order

User = get_user_model()

class POSSession(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    
    cashier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pos_sessions')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    opening_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'pos_sessions'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"POS Session #{self.id} - {self.cashier.username} ({self.start_time.date()})"

class QuickSale(models.Model):
    PAYMENT_METHOD = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Payment'),
    ]
    
    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='sales')
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD, default='cash')
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='quick_sale')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quick_sales'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Quick Sale #{self.id} - {self.total_amount}"
    
    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.subtotal + self.tax - self.discount
        if not self.change_amount:
            self.change_amount = self.amount_paid - self.total_amount
        super().save(*args, **kwargs)

class QuickSaleItem(models.Model):
    sale = models.ForeignKey(QuickSale, on_delete=models.CASCADE, related_name='items')
    cake = models.ForeignKey(Cake, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    customization_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'quick_sale_items'
    
    def __str__(self):
        return f"{self.quantity}x {self.cake.name} - Sale #{self.sale.id}"
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pos_customers'
    
    def __str__(self):
        return f"{self.name} ({self.phone})"

class DailySales(models.Model):
    date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    cash_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    card_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mobile_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'daily_sales'
        ordering = ['-date']
    
    def __str__(self):
        return f"Daily Sales - {self.date} (${self.total_sales})"
