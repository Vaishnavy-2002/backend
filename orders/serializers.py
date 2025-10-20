from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, ShippingAddress, Payment
from cakes.serializers import CakeSerializer
from users.serializers import UserSerializer
from cakes.models import Cake
from django.utils import timezone

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'first_name', 'last_name', 'phone', 'address_line1', 
            'address_line2', 'city', 'state', 'postal_code', 'country', 
            'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'country': {'required': False},
            'phone': {'required': False, 'allow_blank': True}
        }
    
    def create(self, validated_data):
        # Country is optional, no default assignment
        return super().create(validated_data)

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_method', 'payment_status', 'transaction_id', 
            'amount', 'currency', 'payment_date', 'failure_reason', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'payment_status', 'transaction_id', 'payment_date', 'created_at', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    cake = CakeSerializer(read_only=True)
    cake_id = serializers.IntegerField(write_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'cake', 'cake_id', 'quantity', 'unit_price', 'total_price', 'customization_notes']

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    updated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'notes', 'updated_by', 'created_at']
        read_only_fields = ['updated_by', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    customer = UserSerializer(read_only=True)
    customer_info = serializers.SerializerMethodField()
    delivery_person = UserSerializer(read_only=True)
    assigned_staff = UserSerializer(read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    
    def get_customer_info(self, obj):
        """
        Get customer information with display name
        """
        if obj.customer:
            return {
                'id': obj.customer.id,
                'username': obj.customer.username,
                'email': obj.customer.email,
                'first_name': obj.customer.first_name,
                'last_name': obj.customer.last_name,
                'full_name': obj.customer.get_full_name(),
                'display_name': self._get_customer_display_name(obj.customer),
                'is_registered': True,
                'is_guest': obj.is_guest_order
            }
        return {
            'id': None,
            'username': None,
            'email': obj.guest_email,
            'first_name': None,
            'last_name': None,
            'full_name': None,
            'display_name': 'Anonymous',
            'is_registered': False,
            'is_guest': obj.is_guest_order
        }
    
    def _get_customer_display_name(self, customer):
        """
        Get display name for customer
        """
        if customer.first_name and customer.last_name:
            return f"{customer.first_name} {customer.last_name}"
        elif customer.first_name:
            return customer.first_name
        elif customer.username:
            return customer.username
        else:
            return customer.email.split('@')[0] if customer.email else "User"
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        print(f"OrderSerializer serializing order {instance.id} with {instance.items.count()} items")
        return data
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_info', 'order_type', 'order_status', 
            'payment_status', 'payment_method', 'shipping_address', 'delivery_address', 
            'delivery_instructions', 'delivery_person', 'delivery_date', 
            'delivery_time', 'subtotal', 'tax', 'delivery_fee', 'total_amount',
            'created_at', 'updated_at', 'confirmed_at', 'delivered_at',
            'assigned_staff', 'items', 'status_history', 'payment',
            'is_guest_order', 'guest_email', 'guest_phone'
        ]
        read_only_fields = [
            'order_number', 'subtotal', 'tax', 'delivery_fee', 'total_amount',
            'created_at', 'updated_at', 'confirmed_at', 'delivered_at'
        ]

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    shipping_address_id = serializers.IntegerField(required=False)
    shipping_address = ShippingAddressSerializer(required=False)
    is_guest_order = serializers.BooleanField(default=False)
    guest_email = serializers.EmailField(required=False, allow_null=True)
    guest_phone = serializers.CharField(required=False, max_length=20, allow_null=True, allow_blank=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'order_type', 'order_status', 'shipping_address_id', 
            'shipping_address', 'delivery_address', 'delivery_instructions', 'delivery_date', 'delivery_time', 
            'payment_method', 'subtotal', 'tax', 'delivery_fee', 'total_amount', 'created_at', 'items',
            'is_guest_order', 'guest_email', 'guest_phone'
        ]
        read_only_fields = ['id', 'order_number', 'order_status', 'subtotal', 'tax', 'delivery_fee', 'total_amount', 'created_at']
    
    def create(self, validated_data):
        print(f"OrderCreateSerializer.create called with validated_data: {validated_data}")
        items_data = validated_data.pop('items', [])
        print(f"Items data: {items_data}")
        shipping_address_id = validated_data.pop('shipping_address_id', None)
        shipping_address_data = validated_data.pop('shipping_address', None)
        is_guest_order = validated_data.pop('is_guest_order', False)
        guest_email = validated_data.pop('guest_email', None)
        guest_phone = validated_data.pop('guest_phone', None)
        
        print(f"Shipping address ID: {shipping_address_id}")
        print(f"Is guest order: {is_guest_order}")
        
        # Handle shipping address
        if shipping_address_id and not is_guest_order:
            # For authenticated users, use existing address
            try:
                shipping_address = ShippingAddress.objects.get(
                    id=shipping_address_id, 
                    customer=self.context['request'].user
                )
                validated_data['shipping_address'] = shipping_address
            except ShippingAddress.DoesNotExist:
                pass
        elif shipping_address_data and is_guest_order:
            # For guest orders, create a temporary shipping address
            shipping_address = ShippingAddress.objects.create(
                first_name=shipping_address_data.get('first_name', 'Guest'),
                last_name=shipping_address_data.get('last_name', 'User'),
                phone=guest_phone or shipping_address_data.get('phone', ''),
                address_line1=shipping_address_data.get('address_line1', ''),
                address_line2=shipping_address_data.get('address_line2', ''),
                city=shipping_address_data.get('city', ''),
                state=shipping_address_data.get('state', ''),
                postal_code=shipping_address_data.get('postal_code', ''),
                country=shipping_address_data.get('country', ''),
                customer=None  # No customer for guest orders
            )
            validated_data['shipping_address'] = shipping_address
        
        # Set customer from request context (None for guest orders)
        if 'request' in self.context and not is_guest_order:
            validated_data['customer'] = self.context['request'].user
        elif is_guest_order:
            validated_data['customer'] = None
        else:
            raise serializers.ValidationError("Request context not available")
        
        # Set default values for required financial fields
        validated_data['subtotal'] = 0
        validated_data['tax'] = 0
        validated_data['delivery_fee'] = 0
        validated_data['total_amount'] = 0
        
        # Set guest order fields
        validated_data['is_guest_order'] = is_guest_order
        validated_data['guest_email'] = guest_email
        validated_data['guest_phone'] = guest_phone if guest_phone and guest_phone.strip() else None
        
        try:
            order = Order.objects.create(**validated_data)
            print(f"Order created successfully: {order.id}")
        except Exception as e:
            print(f"Error creating order: {e}")
            raise serializers.ValidationError(f"Failed to create order: {str(e)}")
        
        # Calculate totals
        subtotal = 0
        for item_data in items_data:
            try:
                cake_id = item_data.pop('cake_id')
                print(f"Processing item with cake_id: {cake_id}")
                
                try:
                    cake = Cake.objects.get(id=cake_id)
                    print(f"Found cake: {cake.name}")
                except Cake.DoesNotExist:
                    print(f"Cake with id {cake_id} not found")
                    raise serializers.ValidationError(f"Cake with id {cake_id} not found")
                
                # Use frontend-provided price if available, otherwise use base cake price
                frontend_unit_price = item_data.get('unit_price')
                if frontend_unit_price is not None:
                    unit_price = frontend_unit_price
                else:
                    unit_price = cake.price
                
                quantity = item_data.get('quantity', 1)
                print(f"Quantity: {quantity}, Unit price: {unit_price}")
                
                # Use frontend-provided total price if available, otherwise calculate
                frontend_total_price = item_data.get('total_price')
                if frontend_total_price is not None:
                    total_price = frontend_total_price
                else:
                    total_price = unit_price * quantity
                
                subtotal += total_price
                print(f"Total price for this item: {total_price}")
                
                # Remove price fields from item_data before creating OrderItem
                item_data.pop('unit_price', None)
                item_data.pop('total_price', None)
                
                OrderItem.objects.create(
                    order=order,
                    cake=cake,
                    unit_price=unit_price,
                    total_price=total_price,
                    **item_data
                )
                print(f"OrderItem created successfully for cake {cake.name}")
                
            except Exception as e:
                print(f"Error creating order item: {e}")
                raise serializers.ValidationError(f"Failed to create order item: {str(e)}")
        
        # Calculate order totals (use Decimal for proper calculation)
        from decimal import Decimal
        delivery_fee = Decimal('5.00') if order.order_type == 'online' else Decimal('0')
        total_amount = subtotal + delivery_fee
        
        order.subtotal = subtotal
        order.tax = Decimal('0')  # No tax
        order.delivery_fee = delivery_fee
        order.total_amount = total_amount
        order.save()
        
        # Create initial status history
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            notes='Order created',
            updated_by=self.context['request'].user if self.context.get('request') and not is_guest_order else None
        )
        
        print(f"Order created with {order.items.count()} items")
        for item in order.items.all():
            print(f"Item: {item.cake.name}, Quantity: {item.quantity}, Price: {item.total_price}")
        
        return order

class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'order_status', 'payment_status', 'delivery_person', 
            'assigned_staff', 'delivery_date', 'delivery_time'
        ]

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['status', 'notes']
    
    def create(self, validated_data):
        order = self.context['order']
        user = self.context['request'].user
        
        # Update order status
        order.order_status = validated_data['status']
        if validated_data['status'] == 'confirmed':
            order.confirmed_at = timezone.now()
        elif validated_data['status'] == 'delivered':
            order.delivered_at = timezone.now()
        order.save()
        
        # Create status history
        return OrderStatusHistory.objects.create(
            order=order,
            updated_by=user,
            **validated_data
        )
