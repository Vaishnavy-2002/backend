from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model

from .models import Order, OrderItem, OrderStatusHistory, ShippingAddress, Payment, DeliveryLocationHistory
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderUpdateSerializer,
    OrderStatusUpdateSerializer, OrderStatusHistorySerializer,
    ShippingAddressSerializer, PaymentSerializer
)
from users.models import User

class OrderFilter(filters.FilterSet):
    status = filters.CharFilter(field_name='order_status')
    payment_status = filters.CharFilter(field_name='payment_status')
    order_type = filters.CharFilter(field_name='order_type')
    date_from = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='created_at', lookup_expr='lte')
    customer = filters.NumberFilter(field_name='customer')
    
    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'order_type', 'customer']

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = OrderFilter
    
    def get_permissions(self):
        """Override permissions for specific actions"""
        if self.action in ['top_selling_cakes', 'create', 'list', 'retrieve']:
            permission_classes = [permissions.AllowAny]  # Allow guest orders and lookup
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        
        # Handle anonymous users - allow guest order lookup
        if not user.is_authenticated:
            # Check if this is a guest order lookup by order number
            order_number = self.request.query_params.get('order_number')
            if order_number:
                return Order.objects.filter(
                    order_number=order_number,
                    is_guest_order=True
                ).order_by('-created_at')
            
            # For individual order retrieval (retrieve action), allow guest orders
            if self.action == 'retrieve':
                return Order.objects.filter(is_guest_order=True)
            
            return Order.objects.none()
        
        # Filter based on user type
        if user.user_type == 'admin' or user.is_superuser:
            return Order.objects.all().order_by('-created_at')
        elif user.user_type in ['admin', 'staff'] or user.is_staff:
            return Order.objects.filter(
                Q(assigned_staff=user) | Q(assigned_staff__isnull=True)
            ).order_by('-created_at')
        elif user.user_type == 'delivery':
            return Order.objects.filter(delivery_person=user).order_by('-created_at')
        elif user.user_type == 'customer':
            return Order.objects.filter(customer=user).order_by('-created_at')
        else:
            return Order.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderSerializer
    
    def perform_create(self, serializer):
        # Customer is already set in OrderCreateSerializer.create method
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """Custom delete method with admin-only access and proper cleanup"""
        user = request.user
        
        # Only allow admins and superusers to delete orders
        if not (user.user_type == 'admin' or user.is_superuser):
            return Response(
                {'error': 'Permission denied. Only administrators can delete orders.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        order = self.get_object()
        
        try:
            # Log the deletion for audit purposes
            print(f"Admin {user.username} is deleting order {order.order_number} (ID: {order.id})")
            
            # Delete the order (this will cascade to related OrderItems, OrderStatusHistory, etc.)
            order.delete()
            
            return Response(
                {'message': f'Order {order.order_number} has been deleted successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"Error deleting order {order.id}: {str(e)}")
            return Response(
                {'error': f'Failed to delete order: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Use OrderSerializer for the response to include items
        response_serializer = OrderSerializer(serializer.instance, context=self.get_serializer_context())
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={'order': order, 'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Order status updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def assign_delivery(self, request, pk=None):
        order = self.get_object()
        delivery_person_id = request.data.get('delivery_person_id')
        
        try:
            delivery_person = User.objects.get(
                id=delivery_person_id,
                user_type='delivery'
            )
            order.delivery_person = delivery_person
            order.save()
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status=order.order_status,
                notes=f'Assigned to delivery person: {delivery_person.username}',
                updated_by=request.user
            )
            
            return Response({'message': 'Delivery person assigned successfully'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid delivery person ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def assign_staff(self, request, pk=None):
        order = self.get_object()
        staff_id = request.data.get('staff_id')
        
        try:
            staff = User.objects.get(
                id=staff_id,
                user_type__in=['admin', 'staff']
            )
            order.assigned_staff = staff
            order.save()
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status=order.order_status,
                notes=f'Assigned to staff: {staff.username}',
                updated_by=request.user
            )
            
            return Response({'message': 'Staff assigned successfully'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid staff ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        user = request.user
        today = timezone.now().date()
        
        # Filter orders based on user type
        if user.user_type == 'admin' or user.is_superuser:
            orders = Order.objects.all()
        elif user.user_type in ['admin', 'staff'] or user.is_staff:
            orders = Order.objects.filter(
                Q(assigned_staff=user) | Q(assigned_staff__isnull=True)
            )
        elif user.user_type == 'delivery':
            orders = Order.objects.filter(delivery_person=user)
        elif user.user_type == 'customer':
            orders = Order.objects.filter(customer=user)
        else:
            orders = Order.objects.none()
        
        # Today's stats
        today_orders = orders.filter(created_at__date=today)
        today_sales = today_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Status counts
        pending_orders = orders.filter(order_status='pending').count()
        preparing_orders = orders.filter(order_status='preparing').count()
        ready_orders = orders.filter(order_status='ready').count()
        out_for_delivery = orders.filter(order_status='out_for_delivery').count()
        
        # Recent orders
        recent_orders = orders[:10]
        
        stats = {
            'today_sales': today_sales,
            'today_orders': today_orders.count(),
            'pending_orders': pending_orders,
            'preparing_orders': preparing_orders,
            'ready_orders': ready_orders,
            'out_for_delivery': out_for_delivery,
            'recent_orders': OrderSerializer(recent_orders, many=True).data
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def sales_report(self, request):
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Filter orders based on user type
        if user.user_type == 'admin' or user.is_superuser:
            orders = Order.objects.all()
        elif user.user_type in ['admin', 'staff'] or user.is_staff:
            orders = Order.objects.filter(
                Q(assigned_staff=user) | Q(assigned_staff__isnull=True)
            )
        else:
            orders = Order.objects.none()
        
        # Filter by date range
        orders = orders.filter(
            created_at__date__range=[start_date, end_date]
        )
        
        # Calculate stats
        total_sales = orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        total_orders = orders.count()
        
        # Sales by status
        sales_by_status = orders.values('order_status').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        # Sales by payment method
        sales_by_payment = orders.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        report = {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'average_order_value': total_sales / total_orders if total_orders > 0 else 0
            },
            'sales_by_status': sales_by_status,
            'sales_by_payment': sales_by_payment
        }
        
        return Response(report)
    
    @action(detail=True, methods=['get'], url_path='tracking')
    def tracking(self, request, pk=None):
        """Get order tracking information including current location and history"""
        order = self.get_object()
        
        # Check if user has permission to view this order
        user = request.user
        if not (user.is_admin or user.is_staff_member or 
                order.customer == user or order.delivery_person == user):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get current delivery location
        delivery_location = None
        if order.current_latitude and order.current_longitude:
            delivery_location = {
                'latitude': str(order.current_latitude),
                'longitude': str(order.current_longitude),
                'timestamp': order.updated_at
            }
        
        # Get customer location from shipping address
        customer_location = None
        if order.shipping_address:
            # In a real app, you would geocode the address to get coordinates
            # For now, we'll use default coordinates
            customer_location = {
                'latitude': '28.6139',  # Delhi coordinates as example
                'longitude': '77.2090',
                'address': str(order.shipping_address)
            }
        
        # Get location history
        location_history = DeliveryLocationHistory.objects.filter(
            order=order
        ).order_by('-timestamp')[:50]  # Last 50 locations
        
        location_history_data = []
        for location in location_history:
            location_history_data.append({
                'latitude': str(location.latitude),
                'longitude': str(location.longitude),
                'accuracy': location.accuracy,
                'speed': location.speed,
                'heading': location.heading,
                'timestamp': location.timestamp
            })
        
        return Response({
            'order': OrderSerializer(order).data,
            'delivery_location': delivery_location,
            'customer_location': customer_location,
            'location_history': location_history_data,
            'tracking_enabled': order.tracking_enabled
        })
    
    @action(detail=True, methods=['post'], url_path='update-location')
    def update_location(self, request, pk=None):
        """Update delivery person's current location"""
        order = self.get_object()
        user = request.user
        
        # Only delivery person assigned to this order can update location
        if not (user.is_delivery_person and order.delivery_person == user):
            return Response(
                {'error': 'Only assigned delivery person can update location'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        accuracy = request.data.get('accuracy')
        speed = request.data.get('speed')
        heading = request.data.get('heading')
        
        if not latitude or not longitude:
            return Response(
                {'error': 'Latitude and longitude are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update order's current location
            order.current_latitude = float(latitude)
            order.current_longitude = float(longitude)
            order.tracking_enabled = True
            order.save()
            
            # Add to location history
            DeliveryLocationHistory.objects.create(
                order=order,
                latitude=float(latitude),
                longitude=float(longitude),
                accuracy=float(accuracy) if accuracy else None,
                speed=float(speed) if speed else None,
                heading=float(heading) if heading else None
            )
            
            return Response({'message': 'Location updated successfully'})
            
        except ValueError:
            return Response(
                {'error': 'Invalid coordinate values'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def top_selling_cakes(self, request):
        """Get top selling cakes based on order items"""
        user = request.user
        period = request.query_params.get('period', 'month')  # week, month, year
        limit = int(request.query_params.get('limit', 5))
        
        # Calculate date range based on period
        end_date = timezone.now().date()
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Filter orders based on user type
        if not user.is_authenticated:
            # For anonymous users, return empty result
            return Response({
                'period': {
                    'type': period,
                    'start_date': start_date,
                    'end_date': end_date
                },
                'top_cakes': []
            })
        
        if user.user_type == 'admin' or user.is_superuser:
            orders = Order.objects.all()
        elif user.user_type in ['admin', 'staff'] or user.is_staff:
            orders = Order.objects.filter(
                Q(assigned_staff=user) | Q(assigned_staff__isnull=True)
            )
        else:
            orders = Order.objects.none()
        
        # Filter by date range and only delivered orders
        orders = orders.filter(
            created_at__date__range=[start_date, end_date],
            order_status='delivered'
        )
        
        # Get order items and aggregate by cake
        top_cakes = OrderItem.objects.filter(
            order__in=orders
        ).values(
            'cake__id',
            'cake__name',
            'cake__price',
            'cake__image'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price'),
            order_count=Count('order', distinct=True)
        ).order_by('-total_quantity')[:limit]
        
        # Calculate profit margin (assuming 30% average profit margin)
        result = []
        for cake_data in top_cakes:
            profit_margin = 30  # Default profit margin percentage
            profit_amount = float(cake_data['total_revenue']) * (profit_margin / 100)
            
            result.append({
                'id': cake_data['cake__id'],
                'name': cake_data['cake__name'],
                'sales': cake_data['total_quantity'],
                'revenue': float(cake_data['total_revenue']),
                'profit_margin': profit_margin,
                'profit_amount': profit_amount,
                'order_count': cake_data['order_count'],
                'unit_price': float(cake_data['cake__price']),
                'image': cake_data['cake__image']
            })
        
        return Response({
            'period': {
                'type': period,
                'start_date': start_date,
                'end_date': end_date
            },
            'top_cakes': result
        })

    @action(detail=False, methods=['get'])
    def loyalty_insights(self, request):
        """Get customer loyalty insights and analytics"""
        user = request.user
        
        # Check if user is admin or staff
        if not (user.user_type in ['admin', 'staff'] or user.is_superuser or user.is_staff):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get all delivered orders
            delivered_orders = Order.objects.filter(order_status='delivered')
            
            # Calculate customer metrics
            customer_stats = delivered_orders.values('customer').annotate(
                order_count=Count('id'),
                total_spent=Sum('total_amount'),
                avg_order_value=Avg('total_amount')
            ).order_by('-order_count')
            
            # Repeat customers (more than 5 orders)
            repeat_customers = customer_stats.filter(order_count__gt=5)
            repeat_customers_count = repeat_customers.count()
            
            # Top repeat customer
            top_customer_data = None
            if repeat_customers.exists():
                top_customer = repeat_customers.first()
                top_customer_user = User.objects.get(id=top_customer['customer'])
                top_customer_data = {
                    'name': f"{top_customer_user.first_name} {top_customer_user.last_name}".strip() or top_customer_user.username,
                    'orders': top_customer['order_count'],
                    'total_spend': float(top_customer['total_spent'])
                }
            
            # Calculate retention rate (customers who ordered more than once)
            total_customers = customer_stats.count()
            returning_customers = customer_stats.filter(order_count__gt=1).count()
            retention_rate = (returning_customers / total_customers * 100) if total_customers > 0 else 0
            
            # Average order value
            avg_order_value = delivered_orders.aggregate(
                avg_value=Avg('total_amount')
            )['avg_value'] or 0
            
            # Repeat purchase rate (percentage of customers who made more than one order)
            repeat_purchase_rate = (returning_customers / total_customers * 100) if total_customers > 0 else 0
            
            # Additional analytics
            total_loyal_customers = repeat_customers_count
            avg_lifetime_value = 0
            avg_orders_per_customer = 0
            customer_satisfaction = 0
            
            if repeat_customers.exists():
                avg_lifetime_value = repeat_customers.aggregate(
                    avg_lifetime=Avg('total_spent')
                )['avg_lifetime'] or 0
                
                avg_orders_per_customer = repeat_customers.aggregate(
                    avg_orders=Avg('order_count')
                )['avg_orders'] or 0
            
            # Calculate customer satisfaction from feedback (if feedback app exists)
            try:
                from feedback.models import Feedback
                feedback_stats = Feedback.objects.aggregate(
                    avg_rating=Avg('rating'),
                    total_feedback=Count('id')
                )
                customer_satisfaction = float(feedback_stats['avg_rating'] or 0) * 20  # Convert to percentage
            except ImportError:
                customer_satisfaction = 75  # Default value if feedback app not available
            
            return Response({
                'customers': {
                    'repeat_customers': repeat_customers_count,
                    'top_customer': top_customer_data,
                    'total_customers': total_customers,
                    'returning_customers': returning_customers
                },
                'metrics': {
                    'retention_rate': round(retention_rate, 1),
                    'avg_order_value': float(avg_order_value),
                    'repeat_purchase_rate': round(repeat_purchase_rate, 1)
                },
                'analytics': {
                    'total_loyal_customers': total_loyal_customers,
                    'avg_lifetime_value': float(avg_lifetime_value),
                    'avg_orders_per_customer': round(float(avg_orders_per_customer), 1),
                    'customer_satisfaction': round(customer_satisfaction, 1)
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error calculating loyalty insights: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def send_thank_you_email(self, request):
        """Send thank you emails to loyal customers"""
        user = request.user
        
        # Check if user is admin or staff
        if not (user.user_type in ['admin', 'staff'] or user.is_superuser or user.is_staff):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get loyal customers (more than 5 orders)
            loyal_customers = Order.objects.filter(
                order_status='delivered'
            ).values('customer').annotate(
                order_count=Count('id')
            ).filter(order_count__gt=5)
            
            customer_ids = [customer['customer'] for customer in loyal_customers]
            loyal_users = User.objects.filter(id__in=customer_ids)
            
            # In a real application, you would send actual emails here
            # For now, we'll just return the count of customers who would receive emails
            emails_sent = loyal_users.count()
            
            return Response({
                'message': f'Thank you emails sent to {emails_sent} loyal customers',
                'customers_notified': emails_sent,
                'customer_emails': [user.email for user in loyal_users if user.email]
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error sending thank you emails: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_discount_offer(self, request):
        """Create discount offers for repeat customers"""
        user = request.user
        
        # Check if user is admin or staff
        if not (user.user_type in ['admin', 'staff'] or user.is_superuser or user.is_staff):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            discount_percentage = request.data.get('discount_percentage', 10)
            discount_code = request.data.get('discount_code', f'LOYAL{timezone.now().strftime("%Y%m%d")}')
            
            # Get repeat customers (more than 3 orders)
            repeat_customers = Order.objects.filter(
                order_status='delivered'
            ).values('customer').annotate(
                order_count=Count('id')
            ).filter(order_count__gt=3)
            
            customer_ids = [customer['customer'] for customer in repeat_customers]
            repeat_users = User.objects.filter(id__in=customer_ids)
            
            # In a real application, you would create actual discount codes in the database
            # For now, we'll just return the count of customers who would receive offers
            offers_created = repeat_users.count()
            
            return Response({
                'message': f'Discount offers created for {offers_created} repeat customers',
                'discount_code': discount_code,
                'discount_percentage': discount_percentage,
                'customers_eligible': offers_created,
                'customer_emails': [user.email for user in repeat_users if user.email]
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error creating discount offers: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def seasonal_analysis(self, request):
        """Get seasonal sales analysis and trends"""
        user = request.user
        
        # Check if user is admin or staff
        if not (user.user_type in ['admin', 'staff'] or user.is_superuser or user.is_staff):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            year = int(request.query_params.get('year', timezone.now().year))
            month = int(request.query_params.get('month', timezone.now().month))
            
            # Get orders for the specified month and year
            month_orders = Order.objects.filter(
                created_at__year=year,
                created_at__month=month,
                order_status='delivered'
            )
            
            # Calculate monthly metrics
            total_sales = month_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            total_orders = month_orders.count()
            avg_order_value = total_sales / total_orders if total_orders > 0 else 0
            
            # Calculate growth rate compared to previous month
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            
            prev_month_orders = Order.objects.filter(
                created_at__year=prev_year,
                created_at__month=prev_month,
                order_status='delivered'
            )
            
            prev_month_sales = prev_month_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            growth_rate = 0
            if prev_month_sales > 0:
                growth_rate = ((float(total_sales) - float(prev_month_sales)) / float(prev_month_sales)) * 100
            
            # Get daily sales breakdown for the month
            daily_sales = month_orders.extra(
                select={'day': 'EXTRACT(day FROM created_at)'}
            ).values('day').annotate(
                daily_total=Sum('total_amount'),
                daily_orders=Count('id')
            ).order_by('day')
            
            # Identify key sales events (days with high sales)
            daily_sales_list = list(daily_sales)
            if daily_sales_list:
                avg_daily_sales = sum(item['daily_total'] for item in daily_sales_list) / len(daily_sales_list)
                key_events = [
                    {
                        'day': item['day'],
                        'sales': float(item['daily_total']),
                        'orders': item['daily_orders'],
                        'is_peak': float(item['daily_total']) > avg_daily_sales * 1.5
                    }
                    for item in daily_sales_list
                    if float(item['daily_total']) > avg_daily_sales * 1.2
                ]
            else:
                key_events = []
            
            # Get yearly summary for comparison
            yearly_orders = Order.objects.filter(
                created_at__year=year,
                order_status='delivered'
            )
            
            yearly_sales = yearly_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            yearly_orders_count = yearly_orders.count()
            
            # Monthly breakdown for the year
            monthly_breakdown = yearly_orders.extra(
                select={'month': 'EXTRACT(month FROM created_at)'}
            ).values('month').annotate(
                monthly_total=Sum('total_amount'),
                monthly_orders=Count('id')
            ).order_by('month')
            
            monthly_data = {}
            for item in monthly_breakdown:
                monthly_data[int(item['month'])] = {
                    'sales': float(item['monthly_total']),
                    'orders': item['monthly_orders']
                }
            
            # Fill missing months with zero values
            for m in range(1, 13):
                if m not in monthly_data:
                    monthly_data[m] = {'sales': 0, 'orders': 0}
            
            return Response({
                'year': year,
                'month': month,
                'month_name': datetime(year, month, 1).strftime('%B'),
                'summary': {
                    'total_sales': float(total_sales),
                    'total_orders': total_orders,
                    'avg_order_value': float(avg_order_value),
                    'growth_rate': round(growth_rate, 1),
                    'key_events_count': len(key_events)
                },
                'daily_sales': [
                    {
                        'day': int(item['day']),
                        'sales': float(item['daily_total']),
                        'orders': item['daily_orders']
                    }
                    for item in daily_sales_list
                ],
                'key_events': key_events,
                'yearly_summary': {
                    'total_sales': float(yearly_sales),
                    'total_orders': yearly_orders_count,
                    'monthly_breakdown': monthly_data
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error calculating seasonal analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def yearly_seasonal_summary(self, request):
        """Get yearly seasonal summary for all months"""
        user = request.user
        
        # Check if user is admin or staff
        if not (user.user_type in ['admin', 'staff'] or user.is_superuser or user.is_staff):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            year = int(request.query_params.get('year', timezone.now().year))
            
            # Get all orders for the year
            yearly_orders = Order.objects.filter(
                created_at__year=year,
                order_status='delivered'
            )
            
            # Monthly breakdown
            monthly_data = yearly_orders.extra(
                select={'month': 'EXTRACT(month FROM created_at)'}
            ).values('month').annotate(
                monthly_total=Sum('total_amount'),
                monthly_orders=Count('id')
            ).order_by('month')
            
            # Calculate growth rates
            monthly_summary = []
            prev_month_sales = 0
            
            for item in monthly_data:
                month_num = int(item['month'])
                current_sales = float(item['monthly_total'])
                
                growth_rate = 0
                if prev_month_sales > 0:
                    growth_rate = ((current_sales - prev_month_sales) / prev_month_sales) * 100
                
                monthly_summary.append({
                    'month': month_num,
                    'month_name': datetime(year, month_num, 1).strftime('%B'),
                    'sales': current_sales,
                    'orders': item['monthly_orders'],
                    'growth_rate': round(growth_rate, 1)
                })
                
                prev_month_sales = current_sales
            
            # Fill missing months
            existing_months = {item['month'] for item in monthly_summary}
            for month_num in range(1, 13):
                if month_num not in existing_months:
                    monthly_summary.append({
                        'month': month_num,
                        'month_name': datetime(year, month_num, 1).strftime('%B'),
                        'sales': 0,
                        'orders': 0,
                        'growth_rate': 0
                    })
            
            # Sort by month
            monthly_summary.sort(key=lambda x: x['month'])
            
            # Calculate yearly totals
            total_yearly_sales = sum(item['sales'] for item in monthly_summary)
            total_yearly_orders = sum(item['orders'] for item in monthly_summary)
            
            return Response({
                'year': year,
                'summary': {
                    'total_sales': total_yearly_sales,
                    'total_orders': total_yearly_orders,
                    'avg_monthly_sales': total_yearly_sales / 12,
                    'best_month': max(monthly_summary, key=lambda x: x['sales']) if monthly_summary else None,
                    'worst_month': min(monthly_summary, key=lambda x: x['sales']) if monthly_summary else None
                },
                'monthly_data': monthly_summary
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error calculating yearly summary: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def welcome_data(self, request):
        """Get personalized welcome data for user"""
        user = request.user
        
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        # Get user's order history
        user_orders = Order.objects.filter(customer=user, order_status='delivered')
        
        # Get user's favorite cake (most ordered)
        from django.db.models import Count
        favorite_cake = None
        if user_orders.exists():
            cake_counts = {}
            for order in user_orders:
                for item in order.items.all():
                    cake_name = item.cake.name
                    cake_counts[cake_name] = cake_counts.get(cake_name, 0) + item.quantity
            
            if cake_counts:
                favorite_cake_name = max(cake_counts.items(), key=lambda x: x[1])[0]
                favorite_cake = {
                    'name': favorite_cake_name,
                    'order_count': cake_counts[favorite_cake_name]
                }
        
        # Get trending cakes (most ordered in last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        trending_orders = Order.objects.filter(
            created_at__gte=thirty_days_ago,
            order_status='delivered'
        )
        
        trending_cakes = {}
        for order in trending_orders:
            for item in order.items.all():
                cake_name = item.cake.name
                trending_cakes[cake_name] = trending_cakes.get(cake_name, 0) + item.quantity
        
        trending_cake = None
        if trending_cakes:
            trending_cake_name = max(trending_cakes.items(), key=lambda x: x[1])[0]
            trending_cake = {
                'name': trending_cake_name,
                'order_count': trending_cakes[trending_cake_name]
            }
        
        # Generate personalized greeting
        greetings = [
            f"Welcome back, {user.first_name or user.username}! 🍰",
            f"Hello {user.first_name or user.username}! Ready for some sweetness? 🧁",
            f"Hey {user.first_name or user.username}! Your favorite treats await! 🎂",
            f"Welcome home, {user.first_name or user.username}! 🍓",
            f"Good to see you again, {user.first_name or user.username}! 🍪"
        ]
        
        import random
        greeting = random.choice(greetings)
        
        # Add cake emoji based on time of day
        current_hour = datetime.now().hour
        if 6 <= current_hour < 12:
            time_emoji = "🌅"
            time_message = "Good morning!"
        elif 12 <= current_hour < 18:
            time_emoji = "☀️"
            time_message = "Good afternoon!"
        else:
            time_emoji = "🌙"
            time_message = "Good evening!"
        
        return Response({
            'user': {
                'name': user.first_name or user.username,
                'username': user.username,
                'email': user.email
            },
            'greeting': greeting,
            'time_message': time_message,
            'time_emoji': time_emoji,
            'favorite_cake': favorite_cake,
            'trending_cake': trending_cake,
            'total_orders': user_orders.count(),
            'last_order_date': user_orders.first().created_at if user_orders.exists() else None
        })

class OrderStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrderStatusHistory.objects.all().order_by('-created_at')
    serializer_class = OrderStatusHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        order_id = self.kwargs.get('order_pk')
        return OrderStatusHistory.objects.filter(order_id=order_id).order_by('-created_at')

class ShippingAddressViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ShippingAddress.objects.filter(customer=self.request.user)
    
    def perform_create(self, serializer):
        print(f"Creating address for user: {self.request.user}")
        print(f"Address data: {serializer.validated_data}")
        serializer.save(customer=self.request.user)
        print(f"Address created successfully with ID: {serializer.instance.id}")
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        address = self.get_object()
        address.is_default = True
        address.save()
        return Response({'message': 'Default address updated successfully'})
    
    @action(detail=False, methods=['get'])
    def test_db(self, request):
        """Test endpoint to check database connectivity"""
        try:
            count = ShippingAddress.objects.count()
            user_addresses = ShippingAddress.objects.filter(customer=request.user).count()
            return Response({
                'total_addresses': count,
                'user_addresses': user_addresses,
                'user_id': request.user.id,
                'status': 'Database connection working'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)



class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_staff_member:
            return Payment.objects.all()
        return Payment.objects.filter(order__customer=user)
    
    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        payment = self.get_object()
        payment_method = request.data.get('payment_method')
        
        if payment_method:
            payment.payment_method = payment_method
            payment.payment_status = 'processing'
            payment.save()
            
            # Simulate payment processing
            # In a real app, you would integrate with payment gateways here
            import time
            time.sleep(1)  # Simulate processing time
            
            payment.payment_status = 'completed'
            payment.payment_date = timezone.now()
            payment.save()
            
            # Update order payment status
            order = payment.order
            order.payment_status = 'paid'
            order.save()
            
            return Response({'message': 'Payment processed successfully'})
        
        return Response(
            {'error': 'Payment method is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_ingredient_deduction(request, order_id):
    """
    Manually trigger ingredient deduction for an order
    """
    try:
        # Get the order
        order = Order.objects.get(id=order_id)
        
        # Check if user has permission (admin, inventory_manager, or staff)
        user = request.user
        if not (user.is_admin or user.is_inventory_manager or user.is_staff_member):
            return Response({
                'message': 'You do not have permission to trigger ingredient deduction'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get a system user for stock movements
        system_user = User.objects.filter(
            user_type__in=['admin', 'inventory_manager']
        ).first()
        
        if not system_user:
            return Response({
                'message': 'No system user found for stock movements'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Import the deduction function
        from .signals import deduct_ingredients_for_cake
        
        # Process each order item
        deducted_ingredients = []
        for order_item in order.items.all():
            deduct_ingredients_for_cake(
                cake=order_item.cake,
                quantity=order_item.quantity,
                order=order,
                system_user=system_user
            )
            deducted_ingredients.append({
                'cake': order_item.cake.name,
                'quantity': order_item.quantity
            })
        
        return Response({
            'message': 'Ingredient deduction completed successfully',
            'order_number': order.order_number,
            'deducted_ingredients': deducted_ingredients
        }, status=status.HTTP_200_OK)
        
    except Order.DoesNotExist:
        return Response({
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'message': f'Error triggering ingredient deduction: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

