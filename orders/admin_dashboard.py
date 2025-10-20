from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Order
from users.models import User
from inventory.models import Ingredient
from feedback.models import Feedback


def _get_customer_display_name(order):
    """
    Get display name for customer - registered user name or Anonymous for guests
    """
    if order.customer:
        # Registered user - show their name
        if order.customer.first_name and order.customer.last_name:
            return f"{order.customer.first_name} {order.customer.last_name}"
        elif order.customer.first_name:
            return order.customer.first_name
        elif order.customer.username:
            return order.customer.username
        else:
            return order.customer.email.split('@')[0] if order.customer.email else "Registered User"
    else:
        # Guest user
        return "Anonymous"


def _get_customer_display_name_from_feedback(feedback):
    """
    Get display name for feedback user - registered user name or Anonymous for guests
    """
    if feedback.user:
        # Registered user - show their name
        if feedback.user.first_name and feedback.user.last_name:
            return f"{feedback.user.first_name} {feedback.user.last_name}"
        elif feedback.user.first_name:
            return feedback.user.first_name
        elif feedback.user.username:
            return feedback.user.username
        else:
            return feedback.user.email.split('@')[0] if feedback.user.email else "Registered User"
    else:
        # Guest user
        return "Anonymous"


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard_stats(request):
    """
    Comprehensive dashboard statistics for admin users
    """
    user = request.user
    
    # Check if user is admin
    if not (user.user_type == 'admin' or user.is_superuser):
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get all orders
        all_orders = Order.objects.all()
        
        # Calculate order statistics
        total_orders = all_orders.count()
        total_revenue = all_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Pending orders (pending, confirmed, preparing)
        pending_orders = all_orders.filter(
            order_status__in=['pending', 'confirmed', 'preparing']
        ).count()
        
        # Today's sales
        today = timezone.now().date()
        today_orders = all_orders.filter(created_at__date=today)
        today_sales = today_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Customer statistics - separate registered users and guest users
        registered_customers = User.objects.filter(user_type='customer').count()
        guest_customers = all_orders.filter(is_guest_order=True).values('guest_email').distinct().count()
        total_customers = registered_customers + guest_customers
        
        # Staff statistics
        staff_count = User.objects.filter(user_type__in=['admin', 'staff', 'inventory_manager', 'delivery']).count()
        
        # Active customers (customers who have placed at least one order)
        active_customers = User.objects.filter(
            user_type='customer',
            orders__isnull=False
        ).distinct().count()
        
        # Inventory statistics
        total_ingredients = Ingredient.objects.count()
        low_stock_items = Ingredient.objects.filter(
            current_stock__lte=F('minimum_stock')
        ).count()
        
        # Get low stock alerts
        low_stock_alerts = Ingredient.objects.filter(
            current_stock__lte=F('minimum_stock')
        ).values('name', 'current_stock', 'minimum_stock', 'unit')[:10]
        
        # Recent orders (last 5)
        recent_orders = all_orders.order_by('-created_at')[:5]
        
        # Feedback statistics
        total_feedback = Feedback.objects.count()
        
        # Calculate average rating as total rating points divided by total number of ratings
        # This includes ratings from both registered users and guest users
        total_rating_sum = Feedback.objects.aggregate(
            total_rating=Sum('rating')
        )['total_rating'] or 0
        
        # Calculate average rating: total rating points / total number of ratings
        avg_rating = total_rating_sum / total_feedback if total_feedback > 0 else 0
        
        # Order status breakdown
        order_status_breakdown = {
            'pending': all_orders.filter(order_status='pending').count(),
            'confirmed': all_orders.filter(order_status='confirmed').count(),
            'preparing': all_orders.filter(order_status='preparing').count(),
            'ready': all_orders.filter(order_status='ready').count(),
            'out_for_delivery': all_orders.filter(order_status='out_for_delivery').count(),
            'delivered': all_orders.filter(order_status='delivered').count(),
            'cancelled': all_orders.filter(order_status='cancelled').count(),
        }
        
        # Weekly sales trend (last 7 days)
        weekly_sales = []
        for i in range(7):
            date = today - timedelta(days=i)
            day_sales = all_orders.filter(
                created_at__date=date
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            weekly_sales.append({
                'date': date.strftime('%Y-%m-%d'),
                'sales': day_sales
            })
        
        # Get recent feedback (last 5) with user information
        recent_feedback = Feedback.objects.select_related('user').order_by('-created_at')[:5]
        
        # Calculate rating distribution
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        all_feedback = Feedback.objects.all()
        for feedback in all_feedback:
            if feedback.rating in rating_distribution:
                rating_distribution[feedback.rating] += 1
        
        # Prepare response data
        dashboard_data = {
            'overview': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'total_revenue': total_revenue,
                'total_customers': total_customers,
                'registered_customers': registered_customers,
                'guest_customers': guest_customers,
                'active_customers': active_customers,
                'staff_count': staff_count,
                'today_sales': today_sales,
                'low_stock_items': low_stock_items,
                'total_feedback': total_feedback,
                'avg_rating': round(avg_rating, 2) if avg_rating else 0
            },
            'orders': {
                'recent_orders': [
                    {
                        'id': order.id,
                        'order_number': order.order_number,
                        'customer_name': _get_customer_display_name(order),
                        'customer': {
                            'id': order.customer.id if order.customer else None,
                            'username': order.customer.username if order.customer else None,
                            'email': order.customer.email if order.customer else None,
                            'first_name': order.customer.first_name if order.customer else None,
                            'last_name': order.customer.last_name if order.customer else None,
                            'full_name': order.customer.get_full_name() if order.customer else None,
                            'is_guest': order.is_guest_order
                        },
                        'total_amount': order.total_amount,
                        'order_status': order.order_status,
                        'created_at': order.created_at
                    }
                    for order in recent_orders
                ],
                'status_breakdown': order_status_breakdown
            },
            'inventory': {
                'total_ingredients': total_ingredients,
                'low_stock_alerts': list(low_stock_alerts)
            },
            'analytics': {
                'weekly_sales': weekly_sales
            },
            'feedback': {
                'recent_feedback': [
                    {
                        'id': feedback.id,
                        'rating': feedback.rating,
                        'message': feedback.message,
                        'created_at': feedback.created_at,
                        'user_info': {
                            'id': feedback.user.id if feedback.user else None,
                            'username': feedback.user.username if feedback.user else None,
                            'email': feedback.user.email if feedback.user else None,
                            'first_name': feedback.user.first_name if feedback.user else None,
                            'last_name': feedback.user.last_name if feedback.user else None,
                            'full_name': feedback.user.get_full_name() if feedback.user else None,
                            'display_name': _get_customer_display_name_from_feedback(feedback),
                            'is_registered': feedback.user is not None
                        }
                    }
                    for feedback in recent_feedback
                ],
                'rating_distribution': rating_distribution
            }
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error fetching dashboard data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
