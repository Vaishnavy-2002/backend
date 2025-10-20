from django.shortcuts import render
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Q, Sum, Count, Avg

from .models import (
    Supplier, Ingredient, StockMovement, 
    PurchaseOrder, PurchaseOrderItem, Recipe, RecipeIngredient
)
from .serializers import (
    SupplierSerializer, IngredientSerializer, IngredientCreateSerializer,
    StockMovementSerializer, StockMovementCreateSerializer, PurchaseOrderSerializer,
    PurchaseOrderCreateSerializer, RecipeSerializer, RecipeCreateSerializer
)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by('name')
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_inventory_manager:
            return Supplier.objects.all().order_by('name')
        return Supplier.objects.none()

class IngredientFilter(filters.FilterSet):
    supplier = filters.NumberFilter(field_name='supplier')
    is_low_stock = filters.BooleanFilter(method='filter_low_stock')
    is_active = filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = Ingredient
        fields = ['supplier', 'is_low_stock', 'is_active']
    
    def filter_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(current_stock__lte=models.F('minimum_stock'))
        return queryset

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = IngredientFilter
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_inventory_manager or user.is_staff_member:
            return Ingredient.objects.all().order_by('name')
        return Ingredient.objects.none()
    
    def get_object(self):
        queryset = self.get_queryset()
        if not queryset.exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to access ingredients. Please contact an administrator.")
        return super().get_object()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return IngredientCreateSerializer
        return IngredientSerializer
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        ingredients = self.get_queryset().filter(
            current_stock__lte=models.F('minimum_stock')
        )
        serializer = self.get_serializer(ingredients, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        # Ingredients expiring in the next 30 days
        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        ingredients = self.get_queryset().filter(
            expiry_date__lte=thirty_days_from_now,
            expiry_date__gte=timezone.now().date()
        )
        serializer = self.get_serializer(ingredients, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        ingredients = self.get_queryset()
        
        total_ingredients = ingredients.count()
        low_stock_count = ingredients.filter(
            current_stock__lte=models.F('minimum_stock')
        ).count()
        total_value = ingredients.aggregate(
            total=Sum(models.F('current_stock') * models.F('unit_cost'))
        )['total'] or 0
        
        # Recent movements
        recent_movements = StockMovement.objects.filter(
            ingredient__in=ingredients
        ).order_by('-created_at')[:10]
        
        stats = {
            'total_ingredients': total_ingredients,
            'low_stock_count': low_stock_count,
            'total_value': total_value,
            'recent_movements': StockMovementSerializer(recent_movements, many=True).data
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def cost_analysis_report(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        ingredients = self.get_queryset()
        
        # Get stock movements in the date range
        movements = StockMovement.objects.filter(
            ingredient__in=ingredients,
            created_at__date__range=[start_date, end_date]
        )
        
        # Calculate cost analysis
        total_inventory_value = ingredients.aggregate(
            total=Sum(models.F('current_stock') * models.F('unit_cost'))
        )['total'] or 0
        
        # Cost by supplier
        cost_by_supplier = ingredients.values('supplier__name').annotate(
            total_value=Sum(models.F('current_stock') * models.F('unit_cost')),
            count=Count('id'),
            avg_cost=Avg('unit_cost')
        ).order_by('-total_value')
        
        # Most expensive ingredients
        expensive_ingredients = ingredients.order_by('-unit_cost')[:10]
        
        # Low stock high value items
        low_stock_high_value = ingredients.filter(
            current_stock__lte=models.F('minimum_stock')
        ).order_by('-unit_cost')[:10]
        
        # Movement costs
        total_movement_value = movements.aggregate(
            total=Sum('total_value')
        )['total'] or 0
        
        movement_by_type = movements.values('movement_type').annotate(
            count=Count('id'),
            total_value=Sum('total_value')
        )
        
        report = {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_inventory_value': total_inventory_value,
                'total_movement_value': total_movement_value,
                'total_ingredients': ingredients.count(),
                'low_stock_count': ingredients.filter(
                    current_stock__lte=models.F('minimum_stock')
                ).count()
            },
            'cost_by_supplier': cost_by_supplier,
            'expensive_ingredients': IngredientSerializer(expensive_ingredients, many=True).data,
            'low_stock_high_value': IngredientSerializer(low_stock_high_value, many=True).data,
            'movement_by_type': movement_by_type
        }
        
        return Response(report)
    
    @action(detail=False, methods=['get'])
    def consumption_analysis(self, request):
        """Get ingredient consumption analysis for the visual graph"""
        # Handle both DRF and regular requests
        if hasattr(request, 'query_params'):
            period = request.query_params.get('period', 'week')
        else:
            period = request.GET.get('period', 'week')
        
        # Calculate date range based on period
        end_date = timezone.now().date()
        if period == 'today':
            start_date = end_date
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get stock movements (outbound) for consumption analysis
        movements = StockMovement.objects.filter(
            movement_type__in=['out', 'waste'],
            created_at__date__range=[start_date, end_date]
        )
        
        # Calculate consumption by ingredient
        consumption_data = movements.values(
            'ingredient__name',
            'ingredient__unit',
            'ingredient__current_stock'
        ).annotate(
            total_consumed=Sum('quantity'),
            movement_count=Count('id')
        ).order_by('-total_consumed')
        
        # Calculate total consumption for percentage calculation
        total_consumption = sum(float(item['total_consumed']) for item in consumption_data)
        
        # Prepare data for frontend
        ingredients_data = []
        for item in consumption_data[:10]:  # Top 10 ingredients
            percentage = (float(item['total_consumed']) / total_consumption * 100) if total_consumption > 0 else 0
            
            # Calculate trend (simplified - compare with previous period)
            prev_start = start_date - (end_date - start_date)
            prev_movements = StockMovement.objects.filter(
                ingredient__name=item['ingredient__name'],
                movement_type__in=['out', 'waste'],
                created_at__date__range=[prev_start, start_date]
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            current_consumption = float(item['total_consumed'])
            trend = 0
            if prev_movements > 0:
                trend = ((current_consumption - float(prev_movements)) / float(prev_movements)) * 100
            
            ingredients_data.append({
                'name': item['ingredient__name'],
                'unit': item['ingredient__unit'],
                'current_stock': float(item['ingredient__current_stock']),
                'consumed': current_consumption,
                'percentage': round(percentage, 1),
                'trend': round(trend, 1),
                'movement_count': item['movement_count']
            })
        
        # Calculate wastage analysis
        wastage_movements = StockMovement.objects.filter(
            movement_type='waste',
            created_at__date__range=[start_date, end_date]
        )
        
        wastage_data = wastage_movements.values('ingredient__name').annotate(
            total_wasted=Sum('quantity')
        ).order_by('-total_wasted')
        
        wastage_items = []
        for item in wastage_data[:5]:
            wastage_items.append({
                'name': item['ingredient__name'],
                'wasted': float(item['total_wasted']),
                'percentage': round((float(item['total_wasted']) / total_consumption * 100), 1) if total_consumption > 0 else 0
            })
        
        # Low usage items (ingredients with minimal consumption)
        all_ingredients = Ingredient.objects.filter(is_active=True)
        low_usage_items = []
        
        for ingredient in all_ingredients:
            ingredient_consumption = movements.filter(
                ingredient=ingredient
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            if float(ingredient_consumption) < (total_consumption * 0.05):  # Less than 5% of total consumption
                low_usage_items.append({
                    'name': ingredient.name,
                    'consumed': float(ingredient_consumption),
                    'percentage': round((float(ingredient_consumption) / total_consumption * 100), 1) if total_consumption > 0 else 0
                })
        
        # Sort by consumption and take top 5
        low_usage_items = sorted(low_usage_items, key=lambda x: x['consumed'])[:5]
        
        return Response({
            'period': {
                'type': period,
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_consumption': float(total_consumption),
                'total_ingredients': len(ingredients_data),
                'total_movements': movements.count()
            },
            'ingredients': ingredients_data,
            'wastage': wastage_items,
            'low_usage': low_usage_items
        })
    
    @action(detail=False, methods=['get'])
    def weekly_usage_comparison(self, request):
        """Get weekly usage comparison data"""
        # Handle both DRF and regular requests
        if hasattr(request, 'query_params'):
            weeks = int(request.query_params.get('weeks', 4))
        else:
            weeks = int(request.GET.get('weeks', 4))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Get all ingredients
        ingredients = self.get_queryset()
        
        # Calculate weekly consumption for each ingredient
        weekly_data = []
        
        for ingredient in ingredients:
            weekly_consumption = []
            
            for week_offset in range(weeks):
                week_start = start_date + timedelta(weeks=week_offset)
                week_end = week_start + timedelta(days=6)
                
                # For the last week, include today's movements
                if week_offset == weeks - 1:
                    week_end = timezone.now().date()
                
                # Get consumption for this week
                week_movements = StockMovement.objects.filter(
                    ingredient=ingredient,
                    movement_type__in=['out', 'waste'],
                    created_at__date__range=[week_start, week_end]
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                weekly_consumption.append({
                    'week': f"Week {week_offset + 1}",
                    'start_date': week_start,
                    'end_date': week_end,
                    'consumption': float(week_movements),
                    'value': float(week_movements) * float(ingredient.unit_cost)
                })
            
            # Calculate trend
            if len(weekly_consumption) >= 2:
                first_week = weekly_consumption[0]['consumption']
                last_week = weekly_consumption[-1]['consumption']
                trend = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
            else:
                trend = 0
            
            # Calculate average weekly consumption
            avg_consumption = sum(w['consumption'] for w in weekly_consumption) / len(weekly_consumption)
            
            # Calculate usage percentage: (total_used / current_stock) * 100
            total_used = sum(w['consumption'] for w in weekly_consumption)
            current_stock = float(ingredient.current_stock)
            usage_percentage = (total_used / current_stock * 100) if current_stock > 0 else 0
            
            weekly_data.append({
                'ingredient_id': ingredient.id,
                'ingredient_name': ingredient.name,
                'unit': ingredient.unit,
                'current_stock': float(ingredient.current_stock),
                'unit_cost': float(ingredient.unit_cost),
                'weekly_consumption': weekly_consumption,
                'average_weekly_consumption': round(avg_consumption, 2),
                'trend_percentage': round(trend, 1),
                'usage_percentage': round(usage_percentage, 1),  # New field for usage percentage
                'total_weeks_consumption': sum(w['consumption'] for w in weekly_consumption)
            })
        
        # Sort by total consumption
        weekly_data.sort(key=lambda x: x['total_weeks_consumption'], reverse=True)
        
        return Response({
            'period': {
                'weeks': weeks,
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_ingredients': len(weekly_data),
                'weeks_analyzed': weeks
            },
            'ingredients': weekly_data[:20]  # Top 20 ingredients
        })
    
    @action(detail=False, methods=['get'])
    def wastage_unused_analysis(self, request):
        """Get wastage and unused stock analysis"""
        # Handle both DRF and regular requests
        if hasattr(request, 'query_params'):
            period = request.query_params.get('period', 'month')
        else:
            period = request.GET.get('period', 'month')
        
        # Calculate date range
        end_date = timezone.now().date()
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get wastage data
        wastage_movements = StockMovement.objects.filter(
            movement_type='waste',
            created_at__date__range=[start_date, end_date]
        )
        
        wastage_by_ingredient = wastage_movements.values(
            'ingredient__id',
            'ingredient__name',
            'ingredient__unit',
            'ingredient__unit_cost'
        ).annotate(
            total_wasted=Sum('quantity'),
            waste_count=Count('id'),
            total_waste_value=Sum('total_value')
        ).order_by('-total_wasted')
        
        wastage_items = []
        total_waste_value = 0
        
        for item in wastage_by_ingredient:
            waste_value = float(item['total_waste_value'])
            total_waste_value += waste_value
            
            wastage_items.append({
                'ingredient_id': item['ingredient__id'],
                'ingredient_name': item['ingredient__name'],
                'unit': item['ingredient__unit'],
                'total_wasted': float(item['total_wasted']),
                'waste_count': item['waste_count'],
                'waste_value': waste_value,
                'unit_cost': float(item['ingredient__unit_cost'])
            })
        
        # Get unused stock (ingredients with no movements in the period)
        all_ingredients = self.get_queryset()
        unused_items = []
        
        for ingredient in all_ingredients:
            # Check if ingredient had any movements in the period
            has_movements = StockMovement.objects.filter(
                ingredient=ingredient,
                created_at__date__range=[start_date, end_date]
            ).exists()
            
            if not has_movements and ingredient.current_stock > 0:
                unused_items.append({
                    'ingredient_id': ingredient.id,
                    'ingredient_name': ingredient.name,
                    'unit': ingredient.unit,
                    'current_stock': float(ingredient.current_stock),
                    'unit_cost': float(ingredient.unit_cost),
                    'total_value': float(ingredient.current_stock) * float(ingredient.unit_cost),
                    'days_since_last_movement': self._get_days_since_last_movement(ingredient)
                })
        
        # Sort by value
        unused_items.sort(key=lambda x: x['total_value'], reverse=True)
        
        # Get low usage items (ingredients with minimal consumption)
        low_usage_items = []
        consumption_movements = StockMovement.objects.filter(
            movement_type__in=['out', 'waste'],
            created_at__date__range=[start_date, end_date]
        )
        
        total_consumption = consumption_movements.aggregate(total=Sum('quantity'))['total'] or 0
        
        for ingredient in all_ingredients:
            ingredient_consumption = consumption_movements.filter(
                ingredient=ingredient
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            consumption_percentage = (float(ingredient_consumption) / float(total_consumption) * 100) if total_consumption > 0 else 0
            
            if consumption_percentage < 2:  # Less than 2% of total consumption
                low_usage_items.append({
                    'ingredient_id': ingredient.id,
                    'ingredient_name': ingredient.name,
                    'unit': ingredient.unit,
                    'current_stock': float(ingredient.current_stock),
                    'consumption': float(ingredient_consumption),
                    'consumption_percentage': round(consumption_percentage, 2),
                    'unit_cost': float(ingredient.unit_cost),
                    'total_value': float(ingredient.current_stock) * float(ingredient.unit_cost)
                })
        
        # Sort by consumption percentage
        low_usage_items.sort(key=lambda x: x['consumption_percentage'])
        
        return Response({
            'period': {
                'type': period,
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_waste_value': total_waste_value,
                'total_waste_items': len(wastage_items),
                'unused_items_count': len(unused_items),
                'low_usage_items_count': len(low_usage_items)
            },
            'wastage': wastage_items,
            'unused_stock': unused_items[:15],  # Top 15 unused items
            'low_usage': low_usage_items[:15]   # Top 15 low usage items
        })
    
    def _get_days_since_last_movement(self, ingredient):
        """Helper method to get days since last movement"""
        last_movement = StockMovement.objects.filter(
            ingredient=ingredient
        ).order_by('-created_at').first()
        
        if last_movement:
            return (timezone.now().date() - last_movement.created_at.date()).days
        return 999  # Very high number if no movements
    
    @action(detail=False, methods=['get'])
    def ingredient_breakdown(self, request):
        """Get detailed ingredient breakdown analysis"""
        # Handle both DRF and regular requests
        if hasattr(request, 'query_params'):
            category = request.query_params.get('category', 'all')
        else:
            category = request.GET.get('category', 'all')
        
        ingredients = self.get_queryset()
        
        # Filter by category
        if category == 'low_stock':
            ingredients = ingredients.filter(current_stock__lte=F('minimum_stock'))
        elif category == 'high_value':
            # Top 20% by value
            total_count = ingredients.count()
            top_count = max(1, total_count // 5)
            ingredients = ingredients.annotate(
                total_value=F('current_stock') * F('unit_cost')
            ).order_by('-total_value')[:top_count]
        elif category == 'expiring':
            thirty_days_from_now = timezone.now().date() + timedelta(days=30)
            ingredients = ingredients.filter(
                expiry_date__lte=thirty_days_from_now,
                expiry_date__gte=timezone.now().date()
            )
        
        # Calculate breakdown data
        breakdown_data = []
        
        for ingredient in ingredients:
            # Get recent movements
            recent_movements = StockMovement.objects.filter(
                ingredient=ingredient
            ).order_by('-created_at')[:5]
            
            # Calculate consumption trend (last 30 days vs previous 30 days)
            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            sixty_days_ago = timezone.now().date() - timedelta(days=60)
            
            recent_consumption = StockMovement.objects.filter(
                ingredient=ingredient,
                movement_type__in=['out', 'waste'],
                created_at__date__gte=thirty_days_ago
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            previous_consumption = StockMovement.objects.filter(
                ingredient=ingredient,
                movement_type__in=['out', 'waste'],
                created_at__date__range=[sixty_days_ago, thirty_days_ago]
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            # Calculate trend
            if previous_consumption > 0:
                consumption_trend = ((float(recent_consumption) - float(previous_consumption)) / float(previous_consumption)) * 100
            else:
                consumption_trend = 0 if recent_consumption == 0 else 100
            
            # Calculate stock days remaining
            avg_daily_consumption = float(recent_consumption) / 30 if recent_consumption > 0 else 0
            days_remaining = float(ingredient.current_stock) / avg_daily_consumption if avg_daily_consumption > 0 else 999
            
            # Get supplier info
            supplier_info = {
                'name': ingredient.supplier.name if ingredient.supplier else 'No Supplier',
                'contact': ingredient.supplier.contact_person if ingredient.supplier else None,
                'email': ingredient.supplier.email if ingredient.supplier else None
            }
            
            breakdown_data.append({
                'ingredient_id': ingredient.id,
                'name': ingredient.name,
                'description': ingredient.description,
                'unit': ingredient.unit,
                'current_stock': float(ingredient.current_stock),
                'minimum_stock': float(ingredient.minimum_stock),
                'unit_cost': float(ingredient.unit_cost),
                'total_value': float(ingredient.current_stock) * float(ingredient.unit_cost),
                'location': ingredient.location,
                'expiry_date': ingredient.expiry_date.isoformat() if ingredient.expiry_date else None,
                'is_low_stock': ingredient.is_low_stock,
                'supplier': supplier_info,
                'consumption_trend': round(consumption_trend, 1),
                'days_remaining': round(days_remaining, 1),
                'recent_movements': StockMovementSerializer(recent_movements, many=True).data
            })
        
        # Sort by total value
        breakdown_data.sort(key=lambda x: x['total_value'], reverse=True)
        
        # Calculate summary statistics
        total_value = sum(item['total_value'] for item in breakdown_data)
        low_stock_count = sum(1 for item in breakdown_data if item['is_low_stock'])
        expiring_count = sum(1 for item in breakdown_data if item['expiry_date'] and 
                           datetime.strptime(item['expiry_date'], '%Y-%m-%d').date() <= timezone.now().date() + timedelta(days=30))
        
        return Response({
            'category': category,
            'summary': {
                'total_ingredients': len(breakdown_data),
                'total_value': total_value,
                'low_stock_count': low_stock_count,
                'expiring_count': expiring_count,
                'average_value': total_value / len(breakdown_data) if breakdown_data else 0
            },
            'ingredients': breakdown_data
        })
    
    @action(detail=True, methods=['post'])
    def deduct_stock(self, request, pk=None):
        """
        Manually deduct stock from an ingredient
        """
        ingredient = self.get_object()
        user = request.user
        
        # Check permissions
        if not (user.is_admin or user.is_inventory_manager or user.is_staff_member):
            return Response({
                'message': 'You do not have permission to deduct stock'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get deduction amount from request
        deduction_amount = request.data.get('amount')
        reason = request.data.get('reason', 'Manual deduction')
        
        if not deduction_amount:
            return Response({
                'message': 'Deduction amount is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            deduction_amount = float(deduction_amount)
            if deduction_amount <= 0:
                return Response({
                    'message': 'Deduction amount must be positive'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                'message': 'Invalid deduction amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if we have enough stock
        if ingredient.current_stock < deduction_amount:
            return Response({
                'message': f'Insufficient stock. Available: {ingredient.current_stock} {ingredient.unit}, Requested: {deduction_amount} {ingredient.unit}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Deduct stock
        from decimal import Decimal
        previous_stock = ingredient.current_stock
        deduction_decimal = Decimal(str(deduction_amount))
        new_stock = previous_stock - deduction_decimal
        ingredient.current_stock = new_stock
        ingredient.save()
        
        # Create stock movement record
        StockMovement.objects.create(
            ingredient=ingredient,
            movement_type='out',
            quantity=deduction_decimal,
            previous_stock=previous_stock,
            new_stock=new_stock,
            unit_cost=ingredient.unit_cost,
            total_value=deduction_decimal * ingredient.unit_cost,
            reference=f"MANUAL-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            notes=f"Manual deduction: {reason}",
            created_by=user,
            created_at=timezone.now()
        )
        
        # Return updated ingredient data
        serializer = self.get_serializer(ingredient)
        return Response({
            'message': f'Successfully deducted {deduction_amount} {ingredient.unit} from {ingredient.name}',
            'ingredient': serializer.data,
            'deduction': {
                'amount': deduction_amount,
                'unit': ingredient.unit,
                'previous_stock': float(previous_stock),
                'new_stock': float(new_stock)
            }
        }, status=status.HTTP_200_OK)

class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all().order_by('-created_at')
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_inventory_manager:
            return StockMovement.objects.all().order_by('-created_at')
        return StockMovement.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StockMovementCreateSerializer
        return StockMovementSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def movement_report(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        movements = self.get_queryset().filter(
            created_at__date__range=[start_date, end_date]
        )
        
        # Movement by type
        movement_by_type = movements.values('movement_type').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity'),
            total_value=Sum('total_value')
        )
        
        # Movement by ingredient
        movement_by_ingredient = movements.values(
            'ingredient__name'
        ).annotate(
            count=Count('id'),
            total_quantity=Sum('quantity'),
            total_value=Sum('total_value')
        )
        
        report = {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_movements': movements.count(),
                'total_quantity': movements.aggregate(
                    total=Sum('quantity')
                )['total'] or 0,
                'total_value': movements.aggregate(
                    total=Sum('total_value')
                )['total'] or 0
            },
            'movement_by_type': movement_by_type,
            'movement_by_ingredient': movement_by_ingredient
        }
        
        return Response(report)

class PurchaseOrderFilter(filters.FilterSet):
    supplier = filters.NumberFilter(field_name='supplier')
    status = filters.CharFilter(field_name='status')
    date_from = filters.DateFilter(field_name='order_date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='order_date', lookup_expr='lte')
    
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'status']

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().order_by('-created_at')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PurchaseOrderFilter
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_inventory_manager:
            return PurchaseOrder.objects.all().order_by('-created_at')
        return PurchaseOrder.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseOrderCreateSerializer
        return PurchaseOrderSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Use the read serializer for the response
        response_serializer = PurchaseOrderSerializer(serializer.instance, context=self.get_serializer_context())
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def receive_items(self, request, pk=None):
        purchase_order = self.get_object()
        received_items = request.data.get('received_items', [])
        
        for item_data in received_items:
            item_id = item_data.get('item_id')
            received_quantity = item_data.get('received_quantity')
            
            try:
                po_item = PurchaseOrderItem.objects.get(
                    id=item_id,
                    purchase_order=purchase_order
                )
                po_item.received_quantity = received_quantity
                po_item.save()
                
                # Create stock movement
                if received_quantity > 0:
                    StockMovement.objects.create(
                        ingredient=po_item.ingredient,
                        movement_type='in',
                        quantity=received_quantity,
                        unit_cost=po_item.unit_cost,
                        reference=f"PO #{purchase_order.po_number}",
                        notes=f"Received from purchase order",
                        created_by=request.user
                    )
                
            except PurchaseOrderItem.DoesNotExist:
                continue
        
        # Check if all items are received
        all_received = all(
            item.received_quantity >= item.quantity
            for item in purchase_order.items.all()
        )
        
        if all_received:
            purchase_order.status = 'received'
            purchase_order.delivery_date = timezone.now().date()
            purchase_order.save()
        
        return Response({'message': 'Items received successfully'})
    
    @action(detail=False, methods=['get'])
    def pending_orders(self, request):
        pending_orders = self.get_queryset().filter(
            status__in=['draft', 'sent', 'confirmed']
        )
        serializer = self.get_serializer(pending_orders, many=True)
        return Response(serializer.data)

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('name')
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_inventory_manager:
            return Recipe.objects.all().order_by('name')
        return Recipe.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        return RecipeSerializer
    
    @action(detail=True, methods=['post'])
    def check_availability(self, request, pk=None):
        recipe = self.get_object()
        servings = request.data.get('servings', 1)
        
        unavailable_ingredients = []
        
        for recipe_ingredient in recipe.ingredients.all():
            required_quantity = recipe_ingredient.quantity * servings
            available_quantity = recipe_ingredient.ingredient.current_stock
            
            if available_quantity < required_quantity:
                unavailable_ingredients.append({
                    'ingredient': recipe_ingredient.ingredient.name,
                    'required': required_quantity,
                    'available': available_quantity,
                    'shortage': required_quantity - available_quantity
                })
        
        return Response({
            'recipe': recipe.name,
            'servings': servings,
            'available': len(unavailable_ingredients) == 0,
            'unavailable_ingredients': unavailable_ingredients
        })
