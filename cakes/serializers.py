from rest_framework import serializers
from .models import Cake, Category, CustomCake, Review, CakeSize, CakeShape, Frosting, Topping

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'is_active']

class CakeSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    image = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cake
        fields = '__all__'
    
    def get_image(self, obj):
        if obj.image and hasattr(obj.image, 'url') and obj.image.url:
            return obj.image.url
        # Return default image URL if no image is uploaded
        # Use different default images based on cake name
        if 'chocolate' in obj.name.lower():
            return 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=400&fit=crop'
        elif 'vanilla' in obj.name.lower():
            return 'https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400&h=400&fit=crop'
        elif 'strawberry' in obj.name.lower():
            return 'https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=400&h=400&fit=crop'
        else:
            return 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=400&fit=crop'
    
    def get_rating(self, obj):
        from django.db.models import Avg
        reviews = obj.reviews.all()
        if reviews.exists():
            avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
            return round(avg_rating, 1) if avg_rating else 0
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.count()

class CakeWriteSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Cake
        fields = [
            'id', 'name', 'description', 'price', 'category', 'image',
            'is_available', 'is_customizable', 'ingredients', 'allergens',
            'preparation_time'
        ]

class CustomCakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomCake
        fields = '__all__'

class CakeSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CakeSize
        fields = '__all__'

class CakeShapeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CakeShape
        fields = '__all__'

class FrostingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Frosting
        fields = '__all__'

class ToppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topping
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

class CakeDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    customization_options = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Cake
        fields = '__all__'
    
    def get_image(self, obj):
        if obj.image and hasattr(obj.image, 'url') and obj.image.url:
            return obj.image.url
        # Return default image URL if no image is uploaded
        # Use different default images based on cake name
        if 'chocolate' in obj.name.lower():
            return 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=400&fit=crop'
        elif 'vanilla' in obj.name.lower():
            return 'https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400&h=400&fit=crop'
        elif 'strawberry' in obj.name.lower():
            return 'https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=400&h=400&fit=crop'
        else:
            return 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=400&fit=crop'
    
    def get_customization_options(self, obj):
        return {
            'sizes': CakeSizeSerializer(CakeSize.objects.filter(is_active=True), many=True).data,
            'shapes': CakeShapeSerializer(CakeShape.objects.filter(is_active=True), many=True).data,
            'frostings': FrostingSerializer(Frosting.objects.filter(is_active=True), many=True).data,
            'toppings': ToppingSerializer(Topping.objects.filter(is_active=True), many=True).data,
        }
