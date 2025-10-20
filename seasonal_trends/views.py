from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import date, datetime
from .models import SeasonalEvent
from .serializers import SeasonalEventSerializer, SeasonalEventListSerializer


class SeasonalEventViewSet(viewsets.ModelViewSet):
    """ViewSet for managing seasonal events"""
    
    queryset = SeasonalEvent.objects.filter(is_active=True)
    serializer_class = SeasonalEventSerializer
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SeasonalEventListSerializer
        return SeasonalEventSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = SeasonalEvent.objects.filter(is_active=True)
        
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            try:
                year = int(year)
                queryset = queryset.filter(year=year)
            except ValueError:
                pass
        
        # Filter by month
        month = self.request.query_params.get('month')
        if month:
            try:
                month = int(month)
                queryset = queryset.filter(month=month)
            except ValueError:
                pass
        
        # Filter by sales level
        sales_level = self.request.query_params.get('sales_level')
        if sales_level:
            queryset = queryset.filter(sales_level=sales_level)
        
        return queryset.order_by('month', 'day')
    
    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly summary data for seasonal events"""
        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month')
        
        try:
            year = int(year)
            if month:
                month = int(month)
        except ValueError:
            return Response(
                {"error": "Invalid year or month parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get events for the specified year
        events = SeasonalEvent.objects.filter(year=year, is_active=True)
        
        if month:
            events = events.filter(month=month)
        
        # Calculate summary statistics
        total_events = events.count()
        total_revenue = events.aggregate(total=Sum('expected_revenue'))['total'] or 0
        avg_growth_rate = events.aggregate(avg=Sum('growth_rate'))['avg'] or 0
        
        if total_events > 0:
            avg_growth_rate = avg_growth_rate / total_events
        
        # Group by month for monthly breakdown
        monthly_data = {}
        for event in events:
            month_key = event.month
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month': month_key,
                    'month_name': event.get_month_name(),
                    'events_count': 0,
                    'total_revenue': 0,
                    'avg_growth_rate': 0,
                    'sales_levels': {}
                }
            
            monthly_data[month_key]['events_count'] += 1
            monthly_data[month_key]['total_revenue'] += float(event.expected_revenue)
            monthly_data[month_key]['avg_growth_rate'] += event.growth_rate
            
            # Count sales levels
            sales_level = event.sales_level
            if sales_level not in monthly_data[month_key]['sales_levels']:
                monthly_data[month_key]['sales_levels'][sales_level] = 0
            monthly_data[month_key]['sales_levels'][sales_level] += 1
        
        # Calculate averages
        for month_data in monthly_data.values():
            if month_data['events_count'] > 0:
                month_data['avg_growth_rate'] = month_data['avg_growth_rate'] / month_data['events_count']
        
        return Response({
            'year': year,
            'month': month,
            'summary': {
                'total_events': total_events,
                'total_revenue': float(total_revenue),
                'avg_growth_rate': float(avg_growth_rate)
            },
            'monthly_data': list(monthly_data.values())
        })
    
    @action(detail=False, methods=['get'])
    def calendar_data(self, request):
        """Get calendar data for a specific month and year"""
        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month', timezone.now().month)
        
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return Response(
                {"error": "Invalid year or month parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get events for the specified month and year
        events = SeasonalEvent.objects.filter(
            year=year,
            month=month,
            is_active=True
        ).order_by('day')
        
        # Serialize events
        serializer = SeasonalEventListSerializer(events, many=True)
        
        # Calculate month summary
        total_revenue = events.aggregate(total=Sum('expected_revenue'))['total'] or 0
        avg_growth_rate = events.aggregate(avg=Sum('growth_rate'))['avg'] or 0
        events_count = events.count()
        
        if events_count > 0:
            avg_growth_rate = avg_growth_rate / events_count
        
        return Response({
            'year': year,
            'month': month,
            'month_name': events.first().get_month_name() if events.exists() else '',
            'summary': {
                'total_events': events_count,
                'total_revenue': float(total_revenue),
                'avg_growth_rate': float(avg_growth_rate)
            },
            'events': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def upcoming_events(self, request):
        """Get upcoming seasonal events"""
        days_ahead = int(request.query_params.get('days', 30))
        current_date = timezone.now().date()
        
        # Calculate date range
        from datetime import timedelta
        end_date = current_date + timedelta(days=days_ahead)
        
        # Get upcoming events
        events = SeasonalEvent.objects.filter(
            is_active=True,
            year__gte=current_date.year
        ).filter(
            Q(year=current_date.year, month=current_date.month, day__gte=current_date.day) |
            Q(year=current_date.year, month__gt=current_date.month) |
            Q(year__gt=current_date.year)
        ).order_by('year', 'month', 'day')[:10]  # Limit to 10 events
        
        serializer = SeasonalEventListSerializer(events, many=True)
        
        return Response({
            'current_date': current_date,
            'days_ahead': days_ahead,
            'events': serializer.data
        })