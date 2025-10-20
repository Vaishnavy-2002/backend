from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q, F, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from orders.models import Order
from users.models import User
from feedback.models import Feedback
from pos.models import DailySales, QuickSale
from offers.models import Offer
from seasonal_trends.models import SeasonalEvent
from inventory.models import Ingredient


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_analytics(request):
    """
    Comprehensive analytics dashboard data for admin users
    Returns real-time data for Sales Growth, Customer Retention, and Active Campaigns
    """
    user = request.user
    
    # Check if user is admin
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        now = timezone.now()
        today = now.date()
        
        # Calculate Sales Growth (comparing current month vs previous month)
        current_month_start = today.replace(day=1)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)
        
        current_month_sales = Order.objects.filter(
            created_at__date__gte=current_month_start,
            order_status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        previous_month_sales = Order.objects.filter(
            created_at__date__gte=previous_month_start,
            created_at__date__lte=previous_month_end,
            order_status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Calculate sales growth percentage
        if previous_month_sales > 0:
            sales_growth = ((current_month_sales - previous_month_sales) / previous_month_sales) * 100
        else:
            sales_growth = 100 if current_month_sales > 0 else 0
        
        # Calculate Customer Retention (customers who ordered in last 30 days vs previous 30 days)
        thirty_days_ago = today - timedelta(days=30)
        sixty_days_ago = today - timedelta(days=60)
        
        recent_customers = User.objects.filter(
            user_type='customer',
            orders__created_at__date__gte=thirty_days_ago,
            orders__order_status='delivered'
        ).distinct().count()
        
        previous_customers = User.objects.filter(
            user_type='customer',
            orders__created_at__date__gte=sixty_days_ago,
            orders__created_at__date__lt=thirty_days_ago,
            orders__order_status='delivered'
        ).distinct().count()
        
        # Calculate retention rate
        if previous_customers > 0:
            customer_retention = (recent_customers / previous_customers) * 100
        else:
            customer_retention = 100 if recent_customers > 0 else 0
        
        # Count Active Campaigns (offers that are currently active)
        active_campaigns = Offer.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now
        ).count()
        
        # Additional analytics data
        total_orders = Order.objects.count()
        total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
        total_customers = User.objects.filter(user_type='customer').count()
        
        # Today's stats
        today_orders = Order.objects.filter(created_at__date=today).count()
        today_revenue = Order.objects.filter(
            created_at__date=today,
            order_status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Recent orders for quick overview
        recent_orders = Order.objects.order_by('-created_at')[:5]
        
        # Low stock alerts
        low_stock_items = Ingredient.objects.filter(
            current_stock__lte=F('minimum_stock')
        ).count()
        
        # Average order value
        avg_order_value = Order.objects.filter(
            order_status='delivered'
        ).aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Response data
        analytics_data = {
            'quick_overview': {
                'sales_growth': round(sales_growth, 1),
                'customer_retention': round(customer_retention, 1),
                'active_campaigns': active_campaigns,
                'last_sync': now.strftime('%H:%M:%S')
            },
            'summary': {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'total_customers': total_customers,
                'today_orders': today_orders,
                'today_revenue': float(today_revenue),
                'avg_order_value': float(avg_order_value),
                'low_stock_items': low_stock_items
            },
            'recent_orders': [
                {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer.get_full_name() if order.customer else 'Guest',
                    'total_amount': float(order.total_amount),
                    'order_status': order.order_status,
                    'created_at': order.created_at.isoformat()
                }
                for order in recent_orders
            ]
        }
        
        return Response(analytics_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error fetching analytics data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_analytics(request):
    """
    Detailed sales analytics for the Sales Analytics card
    """
    user = request.user
    
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        now = timezone.now()
        today = now.date()
        
        # Sales performance over time (last 30 days)
        sales_data = []
        for i in range(30):
            date = today - timedelta(days=i)
            day_sales = Order.objects.filter(
                created_at__date=date,
                order_status='delivered'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            sales_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'sales': float(day_sales),
                'orders': Order.objects.filter(created_at__date=date).count()
            })
        
        # Top performing products (cakes)
        from cakes.models import Cake
        top_products = []
        for cake in Cake.objects.all():
            total_sold = Order.objects.filter(
                orderitems__cake=cake,
                order_status='delivered'
            ).aggregate(total=Sum('orderitems__quantity'))['total'] or 0
            
            if total_sold > 0:
                revenue = Order.objects.filter(
                    orderitems__cake=cake,
                    order_status='delivered'
                ).aggregate(total=Sum('orderitems__total_price'))['total'] or 0
                
                top_products.append({
                    'id': cake.id,
                    'name': cake.name,
                    'total_sold': total_sold,
                    'revenue': float(revenue),
                    'image': cake.image.url if cake.image else None
                })
        
        # Sort by revenue and take top 10
        top_products.sort(key=lambda x: x['revenue'], reverse=True)
        top_products = top_products[:10]
        
        # Profit margins calculation (simplified)
        total_revenue = Order.objects.filter(
            order_status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Estimate profit margin (assuming 30% profit margin)
        estimated_profit = total_revenue * Decimal('0.30')
        
        # Monthly comparison
        current_month_start = today.replace(day=1)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)
        
        current_month_revenue = Order.objects.filter(
            created_at__date__gte=current_month_start,
            order_status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        previous_month_revenue = Order.objects.filter(
            created_at__date__gte=previous_month_start,
            created_at__date__lte=previous_month_end,
            order_status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        sales_analytics_data = {
            'sales_performance': sales_data,
            'top_products': top_products,
            'profit_analysis': {
                'total_revenue': float(total_revenue),
                'estimated_profit': float(estimated_profit),
                'profit_margin_percentage': 30.0
            },
            'monthly_comparison': {
                'current_month': float(current_month_revenue),
                'previous_month': float(previous_month_revenue),
                'growth_percentage': float(((current_month_revenue - previous_month_revenue) / previous_month_revenue * 100) if previous_month_revenue > 0 else 0)
            }
        }
        
        return Response(sales_analytics_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error fetching sales analytics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seasonal_trends(request):
    """
    Seasonal trends data for the Seasonal Trends card
    """
    user = request.user
    
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        now = timezone.now()
        current_month = now.month
        
        # Get seasonal events for current and upcoming months
        seasonal_events = SeasonalEvent.objects.filter(
            is_active=True,
            month__gte=current_month
        ).order_by('month', 'day')
        
        # Calculate seasonal sales patterns
        seasonal_sales = []
        for month in range(1, 13):
            month_sales = Order.objects.filter(
                created_at__month=month,
                order_status='delivered'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            seasonal_sales.append({
                'month': month,
                'month_name': [
                    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
                ][month - 1],
                'sales': float(month_sales)
            })
        
        # Upcoming events
        upcoming_events = []
        for event in seasonal_events[:5]:  # Next 5 events
            upcoming_events.append({
                'id': event.id,
                'name': event.name,
                'date': event.formatted_date,
                'month': event.month,
                'day': event.day,
                'sales_level': event.sales_level,
                'expected_revenue': float(event.expected_revenue),
                'growth_rate': float(event.growth_rate),
                'products': event.products,
                'icon': event.icon,
                'color': event.color
            })
        
        # Inventory optimization suggestions based on seasonal trends
        inventory_suggestions = []
        for event in seasonal_events[:3]:
            inventory_suggestions.append({
                'event': event.name,
                'suggestion': f"Increase stock for {event.products}",
                'priority': 'high' if event.sales_level in ['high', 'peak'] else 'medium'
            })
        
        seasonal_data = {
            'seasonal_sales_pattern': seasonal_sales,
            'upcoming_events': upcoming_events,
            'inventory_suggestions': inventory_suggestions,
            'current_month_trend': seasonal_sales[current_month - 1] if current_month <= 12 else None
        }
        
        return Response(seasonal_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error fetching seasonal trends: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_loyalty(request):
    """
    Comprehensive customer loyalty analytics for the Loyalty Insights page
    """
    user = request.user
    
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        now = timezone.now()
        today = now.date()
        
        # Time periods for analysis
        thirty_days_ago = today - timedelta(days=30)
        ninety_days_ago = today - timedelta(days=90)
        one_year_ago = today - timedelta(days=365)
        
        # Get all customers with their order data
        customers = User.objects.filter(user_type='customer').annotate(
            total_orders=Count('orders'),
            total_spent=Sum('orders__total_amount'),
            avg_order_value=Avg('orders__total_amount'),
            last_order_date=Max('orders__created_at'),
            first_order_date=Min('orders__created_at')
        ).filter(total_spent__gt=0)
        
        # Calculate repeat customers (more than 5 orders to match frontend text)
        repeat_customers = customers.filter(total_orders__gt=5).count()
        
        # Calculate top repeat customer (most orders, with 5+ orders)
        top_customer = customers.filter(total_orders__gt=5).order_by('-total_orders').first()
        
        # Calculate total customers
        total_customers = customers.count()
        
        # Calculate returning customers (ordered before 30 days ago and again in last 30 days)
        returning_customers = customers.filter(
            orders__created_at__date__lt=thirty_days_ago,
            orders__created_at__date__gte=thirty_days_ago
        ).distinct().count()
        
        # Calculate retention rate
        customers_with_multiple_orders = customers.filter(total_orders__gt=1).count()
        retention_rate = (customers_with_multiple_orders / total_customers * 100) if total_customers > 0 else 0
        
        # Calculate average order value
        avg_order_value = customers.aggregate(avg=Avg('avg_order_value'))['avg'] or 0
        
        # Calculate repeat purchase rate
        repeat_purchase_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
        
        # Calculate average lifetime value
        avg_lifetime_value = customers.aggregate(avg=Avg('total_spent'))['avg'] or 0
        
        # Calculate average orders per customer
        avg_orders_per_customer = customers.aggregate(avg=Avg('total_orders'))['avg'] or 0
        
        # Customer satisfaction analysis (if Feedback model exists)
        try:
            from reviews.models import Review
            feedback_stats = Review.objects.aggregate(
                avg_rating=Avg('rating'),
                total_feedback=Count('id'),
                five_star_count=Count('id', filter=Q(rating=5)),
                four_star_count=Count('id', filter=Q(rating=4)),
                three_star_count=Count('id', filter=Q(rating=3)),
                two_star_count=Count('id', filter=Q(rating=2)),
                one_star_count=Count('id', filter=Q(rating=1))
            )
            customer_satisfaction = round(feedback_stats['avg_rating'] or 0, 1) * 20  # Convert to percentage
        except ImportError:
            # Fallback if Review model doesn't exist
            customer_satisfaction = 85.0  # Default value
        
        # Get top 10 customers by total spent
        top_customers = customers.order_by('-total_spent')[:10]
        top_customers_data = []
        for customer in top_customers:
            top_customers_data.append({
                'id': customer.id,
                'name': customer.get_full_name() or customer.username,
                'email': customer.email,
                'total_orders': customer.total_orders,
                'total_spent': float(customer.total_spent),
                'avg_order_value': float(customer.avg_order_value),
                'last_order_date': customer.last_order_date.isoformat() if customer.last_order_date else None,
                'first_order_date': customer.first_order_date.isoformat() if customer.first_order_date else None
            })
        
        # Get recent repeat customers (ordered multiple times in last 30 days)
        recent_repeat_customers = customers.filter(
            total_orders__gt=1,
            orders__created_at__date__gte=thirty_days_ago
        ).distinct().count()
        
        # Prepare comprehensive response
        loyalty_data = {
            'customers': {
                'repeat_customers': repeat_customers,
                'top_customer': {
                    'name': top_customer.get_full_name() or top_customer.username if top_customer else None,
                    'orders': top_customer.total_orders if top_customer else 0,
                    'total_spend': float(top_customer.total_spent) if top_customer else 0,
                    'email': top_customer.email if top_customer else None
                } if top_customer else None,
                'total_customers': total_customers,
                'returning_customers': returning_customers,
                'recent_repeat_customers': recent_repeat_customers
            },
            'metrics': {
                'retention_rate': round(retention_rate, 1),
                'avg_order_value': round(float(avg_order_value), 2),
                'repeat_purchase_rate': round(repeat_purchase_rate, 1)
            },
            'analytics': {
                'total_loyal_customers': repeat_customers,
                'avg_lifetime_value': round(float(avg_lifetime_value), 2),
                'avg_orders_per_customer': round(float(avg_orders_per_customer), 1),
                'customer_satisfaction': round(customer_satisfaction, 1)
            },
            'top_customers': top_customers_data,
            'summary': {
                'total_revenue': float(customers.aggregate(total=Sum('total_spent'))['total'] or 0),
                'total_orders': customers.aggregate(total=Sum('total_orders'))['total'] or 0,
                'avg_customer_value': round(float(avg_lifetime_value), 2),
                'loyalty_score': round((retention_rate + repeat_purchase_rate + customer_satisfaction) / 3, 1)
            },
            'last_updated': now.isoformat()
        }
        
        return Response(loyalty_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error fetching customer loyalty data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def best_selling_items_analyzer(request):
    """
    Comprehensive best-selling items and profit analyzer
    Returns detailed analytics for the Best-Selling Items & Profit Analyzer page
    """
    user = request.user
    
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        now = timezone.now()
        today = now.date()
        
        # Get period parameter (week, month, year)
        period = request.GET.get('period', 'month')
        
        # Calculate date range based on period
        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:  # month
            start_date = today - timedelta(days=30)
        
        # Get all cakes with their sales data
        from cakes.models import Cake
        from orders.models import OrderItem
        
        cake_analytics = []
        
        for cake in Cake.objects.all():
            # Get orders for this cake in the selected period
            order_items = OrderItem.objects.filter(
                cake=cake,
                order__created_at__date__gte=start_date,
                order__order_status='delivered'
            )
            
            # Calculate metrics
            total_sold = order_items.aggregate(total=Sum('quantity'))['total'] or 0
            total_revenue = order_items.aggregate(total=Sum('total_price'))['total'] or 0
            order_count = order_items.values('order').distinct().count()
            
            # Calculate profit margin (simplified - assuming 30% profit margin)
            profit_margin = 30.0  # This could be made dynamic based on cake cost
            estimated_profit = float(total_revenue) * (profit_margin / 100)
            
            # Get last sale date
            last_sale = order_items.order_by('-order__created_at').first()
            days_since_last_sale = None
            if last_sale:
                days_since_last_sale = (today - last_sale.order.created_at.date()).days
            
            cake_analytics.append({
                'id': cake.id,
                'name': cake.name,
                'sales': total_sold,
                'revenue': float(total_revenue),
                'profit_margin': profit_margin,
                'estimated_profit': estimated_profit,
                'order_count': order_count,
                'days_since_last_sale': days_since_last_sale,
                'image': cake.image.url if cake.image else None,
                'price': float(cake.price),
                'category': cake.category.name if cake.category else 'Uncategorized'
            })
        
        # Sort by sales count (ascending - lowest to highest)
        cake_analytics.sort(key=lambda x: x['sales'], reverse=False)
        
        # Get all cakes (showing all cakes from lowest to highest sales)
        top_cakes = cake_analytics
        
        # Get low performers (cakes with 0 sales)
        low_performers = [
            cake for cake in cake_analytics 
            if cake['sales'] == 0
        ]
        
        # Calculate summary metrics
        total_revenue = sum(cake['revenue'] for cake in cake_analytics)
        total_orders = sum(cake['order_count'] for cake in cake_analytics)
        total_sales = sum(cake['sales'] for cake in cake_analytics)
        
        # Calculate average profit margin
        if cake_analytics:
            avg_profit_margin = sum(cake['profit_margin'] for cake in cake_analytics) / len(cake_analytics)
        else:
            avg_profit_margin = 0
        
        # Get top performer (cake with most sales)
        top_performer = max(cake_analytics, key=lambda x: x['sales']) if cake_analytics else None
        
        # Prepare response
        analyzer_data = {
            'summary': {
                'total_revenue': total_revenue,
                'total_orders': total_orders,
                'total_sales': total_sales,
                'average_profit_margin': round(avg_profit_margin, 1),
                'top_performer': top_performer['name'] if top_performer else 'N/A',
                'period': period,
                'date_range': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
                }
            },
            'top_cakes': top_cakes,
            'low_performers': low_performers,
            'all_cakes': cake_analytics,
            'last_updated': now.isoformat()
        }
        
        return Response(analyzer_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error fetching best-selling items data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profit_analysis(request):
    """
    Detailed profit analysis for individual cakes
    """
    user = request.user
    
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        cake_id = request.GET.get('cake_id')
        if not cake_id:
            return Response(
                {'error': 'cake_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from cakes.models import Cake
        from orders.models import OrderItem
        
        try:
            cake = Cake.objects.get(id=cake_id)
        except Cake.DoesNotExist:
            return Response(
                {'error': 'Cake not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get period parameter
        period = request.GET.get('period', 'month')
        
        # Calculate date range
        today = timezone.now().date()
        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:  # month
            start_date = today - timedelta(days=30)
        
        # Get order items for this cake
        order_items = OrderItem.objects.filter(
            cake=cake,
            order__created_at__date__gte=start_date,
            order__order_status='delivered'
        )
        
        # Calculate detailed metrics
        total_sold = order_items.aggregate(total=Sum('quantity'))['total'] or 0
        total_revenue = order_items.aggregate(total=Sum('total_price'))['total'] or 0
        order_count = order_items.values('order').distinct().count()
        
        # Calculate profit metrics
        profit_margin = 30.0  # This could be made dynamic
        estimated_profit = float(total_revenue) * (profit_margin / 100)
        cost_of_goods_sold = float(total_revenue) - estimated_profit
        
        # Get sales trend (last 7 days)
        sales_trend = []
        for i in range(7):
            date = today - timedelta(days=i)
            day_sales = order_items.filter(
                order__created_at__date=date
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            sales_trend.append({
                'date': date.strftime('%Y-%m-%d'),
                'sales': day_sales
            })
        
        # Get recent orders
        recent_orders = order_items.order_by('-order__created_at')[:10]
        
        profit_analysis_data = {
            'cake': {
                'id': cake.id,
                'name': cake.name,
                'price': float(cake.price),
                'category': cake.category.name if cake.category else 'Uncategorized',
                'image': cake.image.url if cake.image else None
            },
            'metrics': {
                'total_sold': total_sold,
                'total_revenue': float(total_revenue),
                'estimated_profit': estimated_profit,
                'cost_of_goods_sold': cost_of_goods_sold,
                'profit_margin': profit_margin,
                'order_count': order_count,
                'average_order_value': float(total_revenue) / order_count if order_count > 0 else 0
            },
            'sales_trend': sales_trend,
            'recent_orders': [
                {
                    'order_number': item.order.order_number,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price),
                    'order_date': item.order.created_at.isoformat(),
                    'customer_name': item.order.customer.get_full_name() if item.order.customer else 'Guest'
                }
                for item in recent_orders
            ],
            'period': period,
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': today.strftime('%Y-%m-%d')
            }
        }
        
        return Response(profit_analysis_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error fetching profit analysis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def promote_cake(request):
    """
    Create a promotion for a low-performing cake
    """
    user = request.user
    
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        cake_id = request.data.get('cake_id')
        promotion_type = request.data.get('promotion_type', 'percentage')
        discount_value = request.data.get('discount_value', 10)
        duration_days = request.data.get('duration_days', 7)
        
        if not cake_id:
            return Response(
                {'error': 'cake_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from cakes.models import Cake
        from offers.models import Offer
        
        try:
            cake = Cake.objects.get(id=cake_id)
        except Cake.DoesNotExist:
            return Response(
                {'error': 'Cake not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create promotion offer
        from django.utils import timezone
        from datetime import timedelta
        
        offer = Offer.objects.create(
            title=f"Promotion for {cake.name}",
            description=f"Special promotion to boost sales for {cake.name}",
            offer_type=promotion_type,
            discount_percentage=discount_value if promotion_type == 'percentage' else None,
            discount_amount=discount_value if promotion_type == 'fixed' else None,
            minimum_order_amount=0,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=duration_days),
            status='active',
            created_by=user
        )
        
        return Response({
            'message': f'Promotion created successfully for {cake.name}',
            'offer_id': offer.id,
            'offer_title': offer.title,
            'discount_value': discount_value,
            'duration_days': duration_days
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Error creating promotion: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_gratitude_emails(request):
    """
    Send gratitude emails to repeat customers
    """
    user = request.user
    
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get customers with 5+ total orders (consistent with dashboard)
        repeat_customers = User.objects.filter(
            user_type='customer',
            orders__isnull=False
        ).annotate(
            order_count=Count('orders'),
            total_spent=Sum('orders__total_amount')
        ).filter(order_count__gte=5).distinct()
        
        # Debug: Log repeat customers count
        repeat_count = repeat_customers.count()
        print(f"🔍 Debug: Found {repeat_count} customers with 5+ total orders")
        
        if repeat_count == 0:
            # Check what customers we have and their delivered order counts
            all_customers = User.objects.filter(
                user_type='customer',
                orders__isnull=False
            ).annotate(
                total_orders=Count('orders'),
                delivered_orders=Count('orders', filter=Q(orders__order_status='delivered'))
            ).distinct()
            
            print(f"🔍 Debug: All customers with orders:")
            for customer in all_customers:
                print(f"  - {customer.username}: {customer.total_orders} total, {customer.delivered_orders} delivered")
            
            return Response({
                'message': f'No customers found with 5+ total orders to send gratitude emails to',
                'emails_sent': 0,
                'email_details': [],
                'debug_info': f'Found {repeat_count} customers with 5+ total orders'
            }, status=status.HTTP_200_OK)
        
        emails_sent = 0
        email_details = []
        
        for customer in repeat_customers:
            if customer.email:
                # Prepare email content
                subject = f"Thank You for Your Loyalty, {customer.first_name or customer.username}!"
                
                message = f"""
Dear {customer.first_name or customer.username},

We wanted to take a moment to express our heartfelt gratitude for your continued loyalty to SweetBite!

Your support means the world to us, and we're thrilled to have you as one of our valued customers.

Here's a quick summary of your journey with us:
• Total Orders: {customer.order_count}
• Total Spent: Rs {customer.total_spent:,.2f}
• Customer Since: {customer.date_joined.strftime('%B %Y')}

We truly appreciate your trust in our products and services. Your feedback and continued patronage help us improve and grow.

Thank you for being an amazing part of the SweetBite family!

With warm regards,
The SweetBite Team

---
SweetBite - Delicious Cakes for Every Occasion
Email: support@sweetbite.com
Phone: +91 9876543210
                """
                
                # Render HTML email template
                html_message = render_to_string('emails/thank_you.html', {
                    'customer_name': customer.get_full_name() or customer.username,
                    'customer_email': customer.email,
                    'order_count': customer.order_count,
                    'total_spent': customer.total_spent,
                    'date_joined': customer.date_joined.strftime('%B %Y')
                })
                plain_message = strip_tags(html_message)

                # Send the actual email
                try:
                    print(f"📧 Attempting to send email to: {customer.email}")
                    send_mail(
                        subject,
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [customer.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    print(f"✅ Email sent successfully to: {customer.email}")
                    email_details.append({
                        'customer_name': customer.get_full_name() or customer.username,
                        'email': customer.email,
                        'orders': customer.order_count,
                        'total_spent': float(customer.total_spent),
                        'status': 'sent'
                    })
                    emails_sent += 1
                except Exception as e:
                    print(f"❌ Email failed to send to {customer.email}: {str(e)}")
                    email_details.append({
                        'customer_name': customer.get_full_name() or customer.username,
                        'email': customer.email,
                        'orders': customer.order_count,
                        'total_spent': float(customer.total_spent),
                        'status': f'failed: {str(e)}'
                    })
        
        print(f"📊 Final Summary: {emails_sent} emails sent successfully out of {repeat_count} customers")
        
        return Response({
            'message': f'Gratitude emails sent to {emails_sent} repeat customers',
            'emails_sent': emails_sent,
            'email_details': email_details
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error sending gratitude emails: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_special_offers(request):
    """
    Create special offers for repeat customers (10% discount after every 10 orders)
    """
    user = request.user
    
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get customers who have completed 10 or more TOTAL orders
        eligible_customers = User.objects.filter(
            user_type='customer',
            orders__isnull=False
        ).annotate(
            order_count=Count('orders')  # Count all orders, not just delivered
        ).filter(order_count__gte=10).distinct()  # Changed back to 10+ orders
        
        # Debug: Log eligible customers count
        eligible_count = eligible_customers.count()
        print(f"🔍 Debug: Found {eligible_count} customers with 10+ total orders")
        
        # Debug: List all eligible customers
        if eligible_count > 0:
            print(f"🔍 Debug: Eligible customers:")
            for customer in eligible_customers:
                print(f"  - {customer.username}: {customer.order_count} total orders")
        
        if eligible_count == 0:
            # Check what customers we have and their order counts
            all_customers = User.objects.filter(
                user_type='customer',
                orders__isnull=False
            ).annotate(
                total_orders=Count('orders'),
                delivered_orders=Count('orders', filter=Q(orders__order_status='delivered'))
            ).distinct()
            
            print(f"🔍 Debug: All customers with orders:")
            for customer in all_customers:
                print(f"  - {customer.username}: {customer.total_orders} total, {customer.delivered_orders} delivered")
        
        offers_created = 0
        offer_details = []
        
        # Send special discount emails without creating offers (no popups)
        for customer in eligible_customers:
            # Calculate how many 10-order milestones they've reached
            milestones_reached = customer.order_count // 10
            
            # Send email for each milestone (without creating database offers)
            for milestone in range(1, milestones_reached + 1):
                # Generate offer code for email reference
                offer_code = f"SPECIAL{customer.id:03d}{milestone:02d}"
                
                # Send email notification about the special offer
                if customer.email:
                    try:
                        print(f"📧 Sending special offer email to: {customer.email}")
                        
                        subject = f"🎉 Special Discount Just for You, {customer.get_full_name() or customer.username}!"
                        
                        html_message = render_to_string('emails/special_offer.html', {
                            'customer_name': customer.get_full_name() or customer.username,
                            'customer_email': customer.email,
                            'order_count': customer.order_count,
                            'milestone': milestone * 10,
                            'discount_percentage': 10.0,
                            'offer_code': offer_code,
                            'valid_until': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                        })
                        plain_message = strip_tags(html_message)
                        
                        send_mail(
                            subject,
                            plain_message,
                            settings.DEFAULT_FROM_EMAIL,
                            [customer.email],
                            html_message=html_message,
                            fail_silently=False,
                        )
                        print(f"✅ Special offer email sent successfully to: {customer.email}")
                        
                    except Exception as e:
                        print(f"❌ Special offer email failed to send to {customer.email}: {str(e)}")
                
                # Add to offer details for response (email-only, no database offer)
                offer_details.append({
                    'customer_name': customer.get_full_name() or customer.username,
                    'customer_email': customer.email,
                    'orders': customer.order_count,
                    'milestone': milestone * 10,
                    'discount_percentage': 10.0,
                    'offer_code': offer_code,
                    'valid_until': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                    'status': 'email_sent_only'
                })
                offers_created += 1
        
        if offers_created == 0:
            return Response({
                'message': f'No customers eligible for special offers yet (need 10+ total orders)',
                'offers_created': 0,
                'offer_details': [],
                'debug_info': f'Found {eligible_count} customers with 10+ total orders'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': f'Special discount emails sent to {offers_created} customer milestones (no popups created)',
            'offers_created': offers_created,
            'offer_details': offer_details
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error creating special offers: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
