from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta

from .models import POSSession, QuickSale, QuickSaleItem, Customer, DailySales
from .serializers import (
    POSSessionSerializer, POSSessionCreateSerializer, QuickSaleSerializer,
    QuickSaleCreateSerializer, CustomerSerializer, CustomerCreateSerializer,
    DailySalesSerializer, POSDashboardSerializer
)

class POSSessionViewSet(viewsets.ModelViewSet):
    queryset = POSSession.objects.all().order_by('-start_time')
    serializer_class = POSSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['admin', 'staff'] or user.is_superuser or user.is_staff:
            return POSSession.objects.all().order_by('-start_time')
        return POSSession.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return POSSessionCreateSerializer
        return POSSessionSerializer
    
    @action(detail=True, methods=['post'])
    def close_session(self, request, pk=None):
        session = self.get_object()
        closing_amount = request.data.get('closing_amount', 0)
        
        if session.status == 'closed':
            return Response(
                {'error': 'Session is already closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'closed'
        session.end_time = timezone.now()
        session.closing_amount = closing_amount
        session.save()
        
        return Response({'message': 'Session closed successfully'})
    
    @action(detail=False, methods=['get'])
    def active_session(self, request):
        user = request.user
        active_session = POSSession.objects.filter(
            cashier=user,
            status='open'
        ).first()
        
        if active_session:
            serializer = self.get_serializer(active_session)
            return Response(serializer.data)
        return Response(None)

class QuickSaleViewSet(viewsets.ModelViewSet):
    queryset = QuickSale.objects.all().order_by('-created_at')
    serializer_class = QuickSaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['admin', 'staff'] or user.is_superuser or user.is_staff:
            return QuickSale.objects.all().order_by('-created_at')
        return QuickSale.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QuickSaleCreateSerializer
        return QuickSaleSerializer
    
    def perform_create(self, serializer):
        session = self.context.get('session')
        if not session:
            # Get active session or create new one
            session = POSSession.objects.filter(
                cashier=self.request.user,
                status='open'
            ).first()
            
            if not session:
                session = POSSession.objects.create(
                    cashier=self.request.user,
                    opening_amount=0
                )
        
        serializer.save(session=session)
    
    @action(detail=False, methods=['get'])
    def today_sales(self, request):
        today = timezone.now().date()
        sales = self.get_queryset().filter(created_at__date=today)
        
        total_sales = sales.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        total_transactions = sales.count()
        
        # Sales by payment method
        sales_by_payment = sales.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        return Response({
            'date': today,
            'total_sales': total_sales,
            'total_transactions': total_transactions,
            'sales_by_payment': sales_by_payment
        })

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('name')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['admin', 'staff'] or user.is_superuser or user.is_staff:
            return Customer.objects.all().order_by('name')
        return Customer.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CustomerCreateSerializer
        return CustomerSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if query:
            customers = self.get_queryset().filter(
                Q(name__icontains=query) | Q(phone__icontains=query)
            )
        else:
            customers = self.get_queryset()[:10]
        
        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def purchase_history(self, request, pk=None):
        customer = self.get_object()
        
        # Get quick sales for this customer
        quick_sales = QuickSale.objects.filter(
            customer_phone=customer.phone
        ).order_by('-created_at')
        
        # Get online orders for this customer (if they have a user account)
        online_orders = []
        if hasattr(customer, 'user') and customer.user:
            from orders.models import Order
            online_orders = Order.objects.filter(
                customer=customer.user
            ).order_by('-created_at')
        
        return Response({
            'customer': CustomerSerializer(customer).data,
            'quick_sales': QuickSaleSerializer(quick_sales, many=True).data,
            'online_orders': online_orders  # You might want to serialize this too
        })

class DailySalesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailySales.objects.all().order_by('-date')
    serializer_class = DailySalesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['admin', 'staff'] or user.is_superuser or user.is_staff:
            return DailySales.objects.all().order_by('-date')
        return DailySales.objects.none()
    
    @action(detail=False, methods=['get'])
    def sales_report(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        daily_sales = self.get_queryset().filter(
            date__range=[start_date, end_date]
        )
        
        # Calculate totals
        total_sales = daily_sales.aggregate(
            total=Sum('total_sales')
        )['total'] or 0
        
        total_transactions = daily_sales.aggregate(
            total=Sum('total_transactions')
        )['total'] or 0
        
        # Payment method breakdown
        cash_sales = daily_sales.aggregate(
            total=Sum('cash_sales')
        )['total'] or 0
        
        card_sales = daily_sales.aggregate(
            total=Sum('card_sales')
        )['total'] or 0
        
        mobile_sales = daily_sales.aggregate(
            total=Sum('mobile_sales')
        )['total'] or 0
        
        # Average daily sales
        avg_daily_sales = total_sales / daily_sales.count() if daily_sales.count() > 0 else 0
        
        report = {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_sales': total_sales,
                'total_transactions': total_transactions,
                'average_daily_sales': avg_daily_sales,
                'average_order_value': total_sales / total_transactions if total_transactions > 0 else 0
            },
            'payment_breakdown': {
                'cash_sales': cash_sales,
                'card_sales': card_sales,
                'mobile_sales': mobile_sales
            },
            'daily_data': DailySalesSerializer(daily_sales, many=True).data
        }
        
        return Response(report)

class POSDashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        user = request.user
        today = timezone.now().date()
        
        # Get active session
        active_session = POSSession.objects.filter(
            cashier=user,
            status='open'
        ).first()
        
        # Today's sales
        today_sales = QuickSale.objects.filter(
            created_at__date=today
        )
        
        today_total_sales = today_sales.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        today_transactions = today_sales.count()
        
        # Low stock items (from inventory)
        low_stock_items = []
        if user.user_type in ['admin', 'inventory_manager'] or user.is_superuser:
            from inventory.models import Ingredient
            low_stock_items = Ingredient.objects.filter(
                current_stock__lte=models.F('minimum_stock')
            ).values('name', 'current_stock', 'minimum_stock')[:5]
        
        # Recent sales
        recent_sales = QuickSale.objects.filter(
            created_at__date=today
        ).order_by('-created_at')[:10]
        
        dashboard_data = {
            'today_sales': today_total_sales,
            'today_transactions': today_transactions,
            'active_session': POSSessionSerializer(active_session).data if active_session else None,
            'low_stock_items': low_stock_items,
            'recent_sales': QuickSaleSerializer(recent_sales, many=True).data
        }
        
        return Response(dashboard_data)
