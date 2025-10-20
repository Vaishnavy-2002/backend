from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'suppliers'
    
    def __str__(self):
        return self.name

class Ingredient(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('pcs', 'Pieces'),
        ('packs', 'Packs'),
        ('boxes', 'Boxes'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    current_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='ingredients')
    location = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ingredients'
    
    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"
    
    @property
    def total_value(self):
        return self.current_stock * self.unit_cost
    
    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Stock Adjustment'),
        ('waste', 'Waste/Loss'),
    ]
    
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    previous_stock = models.DecimalField(max_digits=10, decimal_places=3)
    new_stock = models.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True)  # Order number, etc.
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ingredient.name} - {self.movement_type} ({self.quantity})"

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed by Supplier'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    po_number = models.CharField(max_length=20, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order_date = models.DateField()
    expected_delivery = models.DateField(blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"PO #{self.po_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            # Generate PO number
            import datetime
            today = datetime.datetime.now()
            last_po = PurchaseOrder.objects.filter(created_at__date=today.date()).order_by('-id').first()
            if last_po:
                last_number = int(last_po.po_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.po_number = f"PO{today.strftime('%Y%m%d')}{new_number:04d}"
        
        super().save(*args, **kwargs)

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'purchase_order_items'
    
    def __str__(self):
        return f"{self.ingredient.name} - {self.quantity} units"
    
    def save(self, *args, **kwargs):
        if not self.total_cost:
            self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

class Recipe(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    servings = models.PositiveIntegerField(default=1)
    instructions = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recipes'
    
    def __str__(self):
        return self.name

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=10, choices=Ingredient.UNIT_CHOICES)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'recipe_ingredients'
    
    def __str__(self):
        return f"{self.ingredient.name} - {self.quantity} {self.unit}"
