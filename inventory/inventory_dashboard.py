from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Ingredient, Supplier, StockMovement
from .serializers import IngredientSerializer, SupplierSerializer, StockMovementSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_dashboard_stats(request):
    """
    Comprehensive inventory dashboard statistics
    """
    user = request.user
    
    # Check if user has inventory access
    if not (user.user_type in ['admin', 'inventory_manager'] or user.is_superuser):
        return Response(
            {'error': 'Access denied. Inventory management privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get all ingredients
        all_ingredients = Ingredient.objects.all()
        
        # Calculate basic statistics
        total_ingredients = all_ingredients.count()
        low_stock_count = all_ingredients.filter(
            current_stock__lte=F('minimum_stock')
        ).count()
        
        # Calculate total inventory value
        total_value = all_ingredients.aggregate(
            total=Sum(F('current_stock') * F('unit_cost'))
        )['total'] or 0
        
        # Get low stock items
        low_stock_items = all_ingredients.filter(
            current_stock__lte=F('minimum_stock')
        ).values('id', 'name', 'current_stock', 'minimum_stock', 'unit', 'unit_cost')
        
        # Get expiring items (next 30 days)
        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        expiring_items = all_ingredients.filter(
            expiry_date__lte=thirty_days_from_now,
            expiry_date__gte=timezone.now().date()
        ).values('id', 'name', 'expiry_date', 'current_stock', 'unit')
        
        # Get suppliers
        suppliers = Supplier.objects.all()
        
        # Get recent stock movements
        recent_movements = StockMovement.objects.filter(
            ingredient__in=all_ingredients
        ).order_by('-created_at')[:10]
        
        # Calculate supplier statistics
        supplier_stats = []
        for supplier in suppliers:
            supplier_ingredients = all_ingredients.filter(supplier=supplier)
            supplier_low_stock = supplier_ingredients.filter(
                current_stock__lte=F('minimum_stock')
            ).count()
            supplier_value = supplier_ingredients.aggregate(
                total=Sum(F('current_stock') * F('unit_cost'))
            )['total'] or 0
            
            supplier_stats.append({
                'id': supplier.id,
                'name': supplier.name,
                'contact_person': supplier.contact_person,
                'email': supplier.email,
                'phone': supplier.phone,
                'total_ingredients': supplier_ingredients.count(),
                'low_stock_count': supplier_low_stock,
                'total_value': supplier_value
            })
        
        # Prepare response data
        dashboard_data = {
            'overview': {
                'total_ingredients': total_ingredients,
                'low_stock_count': low_stock_count,
                'total_value': total_value,
                'expiring_soon_count': expiring_items.count()
            },
            'ingredients': {
                'low_stock_items': list(low_stock_items),
                'expiring_items': list(expiring_items),
                'recent_movements': StockMovementSerializer(recent_movements, many=True).data
            },
            'suppliers': {
                'list': SupplierSerializer(suppliers, many=True).data,
                'stats': supplier_stats
            }
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error fetching inventory dashboard data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
