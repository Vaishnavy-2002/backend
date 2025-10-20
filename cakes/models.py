from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, blank=True)  # Emoji or icon
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class CakeSize(models.Model):
    name = models.CharField(max_length=50, unique=True)
    servings = models.IntegerField()
    price_modifier = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'cake_sizes'

    def __str__(self):
        return f"{self.name} ({self.servings} servings)"

class CakeShape(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price_modifier = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'cake_shapes'

    def __str__(self):
        return self.name

class Frosting(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price_modifier = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    color = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'frostings'

    def __str__(self):
        return self.name

class Topping(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price_modifier = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'toppings'

    def __str__(self):
        return self.name

class Cake(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='cakes')
    image = models.ImageField(upload_to='cakes/')
    is_available = models.BooleanField(default=True)
    is_customizable = models.BooleanField(default=True)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.IntegerField(default=0)
    ingredients = models.JSONField(default=list)
    allergens = models.JSONField(default=list)
    preparation_time = models.CharField(max_length=50, default="2-3 hours")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cakes'

    def __str__(self):
        return self.name

    def calculate_customized_price(self, customizations):
        """Calculate price based on customizations"""
        price = self.price
        
        # Add size modifier
        if customizations.get('size'):
            try:
                size = CakeSize.objects.get(id=customizations['size'])
                price += size.price_modifier
            except CakeSize.DoesNotExist:
                pass
        
        # Add shape modifier
        if customizations.get('shape'):
            try:
                shape = CakeShape.objects.get(id=customizations['shape'])
                price += shape.price_modifier
            except CakeShape.DoesNotExist:
                pass
        
        # Add frosting modifier
        if customizations.get('frosting'):
            try:
                frosting = Frosting.objects.get(id=customizations['frosting'])
                price += frosting.price_modifier
            except Frosting.DoesNotExist:
                pass
        
        # Add toppings
        if customizations.get('toppings'):
            for topping_id in customizations['toppings']:
                try:
                    topping = Topping.objects.get(id=topping_id)
                    price += topping.price_modifier
                except Topping.DoesNotExist:
                    pass
        
        return price

class CustomCake(models.Model):
    base_cake = models.ForeignKey(Cake, on_delete=models.CASCADE, related_name='custom_versions')
    size = models.ForeignKey(CakeSize, on_delete=models.CASCADE, null=True, blank=True)
    shape = models.ForeignKey(CakeShape, on_delete=models.CASCADE, null=True, blank=True)
    frosting = models.ForeignKey(Frosting, on_delete=models.CASCADE, null=True, blank=True)
    toppings = models.ManyToManyField(Topping, blank=True)
    custom_message = models.CharField(max_length=30, blank=True)
    design_notes = models.TextField(blank=True)
    reference_image = models.ImageField(upload_to='custom_cakes/', blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'custom_cakes'

    def __str__(self):
        return f"Custom {self.base_cake.name}"

    def save(self, *args, **kwargs):
        # Calculate total price before saving
        customizations = {
            'size': self.size.id if self.size else None,
            'shape': self.shape.id if self.shape else None,
            'frosting': self.frosting.id if self.frosting else None,
            'toppings': list(self.toppings.values_list('id', flat=True))
        }
        self.total_price = self.base_cake.calculate_customized_price(customizations)
        super().save(*args, **kwargs)

class Review(models.Model):
    cake = models.ForeignKey(Cake, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cake_reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cake_reviews'
        # unique_together = ['cake', 'user']  # Removed to allow multiple reviews per user per cake

    def __str__(self):
        return f"{self.user.username} - {self.cake.name} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update cake rating and review count
        self.update_cake_rating()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # Update cake rating and review count
        self.update_cake_rating()

    def update_cake_rating(self):
        """Update the cake's average rating and review count"""
        reviews = Review.objects.filter(cake=self.cake)
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.cake.rating = round(avg_rating, 2)
            self.cake.review_count = reviews.count()
        else:
            self.cake.rating = 0
            self.cake.review_count = 0
        self.cake.save(update_fields=['rating', 'review_count'])
