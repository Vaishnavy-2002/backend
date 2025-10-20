from rest_framework import serializers
from .models import (
    Supplier, Ingredient, StockMovement, 
    PurchaseOrder, PurchaseOrderItem, Recipe, RecipeIngredient
)
from users.serializers import UserSerializer

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_person', 'email', 'phone', 'address', 
            'website', 'notes', 'is_active', 'created_at'
        ]

class IngredientSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    
    class Meta:
        model = Ingredient
        fields = [
            'id', 'name', 'description', 'unit', 'current_stock',
            'minimum_stock', 'unit_cost', 'supplier', 'location', 'expiry_date',
            'is_active', 'created_at', 'updated_at', 'total_value', 'is_low_stock'
        ]
        read_only_fields = ['total_value', 'is_low_stock']

class IngredientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = [
            'name', 'description', 'unit', 'current_stock',
            'minimum_stock', 'unit_cost', 'supplier', 'location', 'expiry_date'
        ]
        extra_kwargs = {
            'supplier': {'required': False, 'allow_null': True}
        }

class StockMovementSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'ingredient', 'movement_type', 'quantity', 'previous_stock',
            'new_stock', 'unit_cost', 'total_value', 'reference', 'notes',
            'created_by', 'created_at'
        ]
        read_only_fields = ['previous_stock', 'new_stock', 'total_value', 'created_by', 'created_at']

class StockMovementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ['ingredient', 'movement_type', 'quantity', 'unit_cost', 'reference', 'notes']
    
    def create(self, validated_data):
        ingredient = validated_data['ingredient']
        quantity = validated_data['quantity']
        movement_type = validated_data['movement_type']
        
        # Calculate stock changes
        previous_stock = ingredient.current_stock
        
        if movement_type == 'in':
            new_stock = previous_stock + quantity
        elif movement_type == 'out':
            new_stock = previous_stock - quantity
        elif movement_type == 'adjustment':
            new_stock = quantity
        elif movement_type == 'waste':
            new_stock = previous_stock - quantity
        
        # Update ingredient stock
        ingredient.current_stock = new_stock
        ingredient.save()
        
        # Calculate total value
        total_value = quantity * validated_data['unit_cost']
        
        return StockMovement.objects.create(
            ingredient=ingredient,
            previous_stock=previous_stock,
            new_stock=new_stock,
            total_value=total_value,
            created_by=self.context['request'].user,
            **validated_data
        )

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'ingredient', 'quantity', 'unit_cost', 'total_cost',
            'received_quantity', 'notes'
        ]
        read_only_fields = ['total_cost']

class PurchaseOrderItemCreateSerializer(serializers.ModelSerializer):
    ingredient = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'ingredient', 'quantity', 'unit_cost', 'notes'
        ]

class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'status', 'order_date',
            'expected_delivery', 'delivery_date', 'subtotal', 'tax',
            'total_amount', 'notes', 'created_by', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = [
            'po_number', 'subtotal', 'tax', 'total_amount', 'created_by', 'created_at', 'updated_at'
        ]

class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemCreateSerializer(many=True)
    expected_delivery = serializers.DateField(required=False, allow_null=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'order_date', 'expected_delivery', 'notes', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        purchase_order = PurchaseOrder.objects.create(
            **validated_data
        )
        
        # Calculate totals
        from decimal import Decimal
        subtotal = Decimal('0')
        for item_data in items_data:
            total_cost = item_data['quantity'] * item_data['unit_cost']
            subtotal += total_cost
            
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                ingredient_id=item_data['ingredient'],
                quantity=item_data['quantity'],
                unit_cost=item_data['unit_cost'],
                total_cost=total_cost,
                received_quantity=0,
                notes=item_data.get('notes', '')
            )
        
        # Calculate order totals
        total_amount = subtotal
        
        purchase_order.subtotal = subtotal
        purchase_order.tax = Decimal('0')  # No tax
        purchase_order.total_amount = total_amount
        purchase_order.save()
        
        # Return the purchase order with proper serialization
        return purchase_order

class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    
    class Meta:
        model = RecipeIngredient
        fields = ['id', 'ingredient', 'quantity', 'unit', 'notes']

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    
    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'description', 'servings', 'instructions',
            'is_active', 'created_at', 'updated_at', 'ingredients'
        ]

class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    
    class Meta:
        model = Recipe
        fields = ['name', 'description', 'servings', 'instructions', 'ingredients']
    
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient_data)
        
        return recipe
