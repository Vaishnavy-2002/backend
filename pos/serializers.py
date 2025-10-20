from rest_framework import serializers
from .models import POSSession, QuickSale, QuickSaleItem, Customer, DailySales
from cakes.serializers import CakeSerializer
from users.serializers import UserSerializer

class POSSessionSerializer(serializers.ModelSerializer):
    cashier = UserSerializer(read_only=True)
    
    class Meta:
        model = POSSession
        fields = [
            'id', 'cashier', 'start_time', 'end_time', 'opening_amount',
            'closing_amount', 'total_sales', 'total_transactions', 'status', 'notes'
        ]
        read_only_fields = ['cashier', 'start_time', 'end_time', 'total_sales', 'total_transactions']

class POSSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSSession
        fields = ['opening_amount', 'notes']
    
    def create(self, validated_data):
        validated_data['cashier'] = self.context['request'].user
        return super().create(validated_data)

class QuickSaleItemSerializer(serializers.ModelSerializer):
    cake = CakeSerializer(read_only=True)
    cake_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = QuickSaleItem
        fields = ['id', 'cake', 'cake_id', 'quantity', 'unit_price', 'total_price', 'customization_notes']
        read_only_fields = ['unit_price', 'total_price']

class QuickSaleSerializer(serializers.ModelSerializer):
    items = QuickSaleItemSerializer(many=True, read_only=True)
    session = POSSessionSerializer(read_only=True)
    
    class Meta:
        model = QuickSale
        fields = [
            'id', 'session', 'customer_name', 'customer_phone', 'subtotal',
            'tax', 'discount', 'total_amount', 'amount_paid', 'change_amount',
            'payment_method', 'order', 'created_at', 'items'
        ]
        read_only_fields = ['subtotal', 'tax', 'total_amount', 'change_amount', 'created_at']

class QuickSaleCreateSerializer(serializers.ModelSerializer):
    items = QuickSaleItemSerializer(many=True)
    
    class Meta:
        model = QuickSale
        fields = [
            'customer_name', 'customer_phone', 'discount', 'amount_paid',
            'payment_method', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        session = self.context['session']
        
        # Calculate totals
        subtotal = 0
        for item_data in items_data:
            from cakes.models import Cake
            cake_id = item_data.pop('cake_id')
            cake = Cake.objects.get(id=cake_id)
            unit_price = cake.price
            quantity = item_data.get('quantity', 1)
            total_price = unit_price * quantity
            subtotal += total_price
            
            item_data['unit_price'] = unit_price
            item_data['total_price'] = total_price
        
        # Calculate order totals
        discount = validated_data.get('discount', 0)
        total_amount = subtotal - discount
        
        quick_sale = QuickSale.objects.create(
            session=session,
            subtotal=subtotal,
            tax=0,  # No tax
            total_amount=total_amount,
            **validated_data
        )
        
        # Create order items
        for item_data in items_data:
            cake_id = item_data.pop('cake_id')
            cake = Cake.objects.get(id=cake_id)
            QuickSaleItem.objects.create(
                sale=quick_sale,
                cake=cake,
                **item_data
            )
        
        # Update session totals
        session.total_sales += total_amount
        session.total_transactions += 1
        session.save()
        
        return quick_sale

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'phone', 'email', 'address', 'total_orders',
            'total_spent', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_orders', 'total_spent', 'created_at', 'updated_at']

class CustomerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address']

class DailySalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySales
        fields = [
            'id', 'date', 'total_sales', 'total_transactions', 'cash_sales',
            'card_sales', 'mobile_sales', 'average_order_value'
        ]
        read_only_fields = ['average_order_value']

class POSDashboardSerializer(serializers.Serializer):
    today_sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    today_transactions = serializers.IntegerField()
    active_session = POSSessionSerializer()
    low_stock_items = serializers.ListField()
    recent_sales = QuickSaleSerializer(many=True)
