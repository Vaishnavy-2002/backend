from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.utils import timezone
from django.db.models import Q

from .models import Offer
from .serializers import OfferSerializer, OfferCreateSerializer, HomepageOfferSerializer

class OfferFilter(filters.FilterSet):
    status = filters.CharFilter(field_name='status')
    offer_type = filters.CharFilter(field_name='offer_type')
    is_active = filters.BooleanFilter(method='filter_is_active')
    is_homepage_featured = filters.BooleanFilter(field_name='is_homepage_featured')
    is_popup = filters.BooleanFilter(field_name='is_popup')
    
    class Meta:
        model = Offer
        fields = ['status', 'offer_type', 'is_active', 'is_homepage_featured', 'is_popup']
    
    def filter_is_active(self, queryset, name, value):
        """Filter by active status"""
        now = timezone.now()
        if value:
            return queryset.filter(
                status='active',
                start_date__lte=now,
                end_date__gte=now
            )
        else:
            return queryset.exclude(
                status='active',
                start_date__lte=now,
                end_date__gte=now
            )

class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = [permissions.AllowAny]  # Allow public access by default
    filterset_class = OfferFilter
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return OfferCreateSerializer
        return OfferSerializer
    
    def get_queryset(self):
        """Filter offers based on user permissions"""
        user = self.request.user
        
        if user.is_admin:
            return Offer.objects.all()
        else:
            # Regular users can only see active offers
            now = timezone.now()
            return Offer.objects.filter(
                status='active',
                start_date__lte=now,
                end_date__gte=now
            )
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['list', 'retrieve', 'homepage', 'popup']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]  # Default to AllowAny for public actions
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def homepage(self, request):
        """Get offers for homepage display"""
        now = timezone.now()
        
        # Get active offers that are featured on homepage
        offers = Offer.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now,
            is_homepage_featured=True
        ).order_by('-created_at')
        
        # Filter by user type if user is authenticated
        if request.user.is_authenticated:
            user_type = request.user.user_type
            offers = offers.filter(
                Q(target_user_types__isnull=True) | 
                Q(target_user_types__contains=[user_type]) |
                Q(target_user_types__contains=[])
            )
        
        serializer = HomepageOfferSerializer(offers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def popup(self, request):
        """Get popup offers for homepage"""
        now = timezone.now()
        
        # Get active popup offers
        popup_offers = Offer.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now,
            is_popup=True
        ).order_by('-created_at')
        
        # Filter by user type if user is authenticated
        if request.user.is_authenticated:
            user_type = request.user.user_type
            popup_offers = popup_offers.filter(
                Q(target_user_types__isnull=True) | 
                Q(target_user_types__contains=[user_type]) |
                Q(target_user_types__contains=[])
            )
        
        serializer = HomepageOfferSerializer(popup_offers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request, pk=None):
        """Apply offer to an order"""
        offer = self.get_object()
        order_amount = request.data.get('order_amount', 0)
        
        if not offer.can_be_used_by(request.user):
            return Response(
                {'error': 'This offer cannot be used'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        discount_amount = offer.calculate_discount(order_amount)
        
        if discount_amount > 0:
            # Increment usage count
            offer.usage_count += 1
            offer.save()
            
            return Response({
                'success': True,
                'discount_amount': discount_amount,
                'offer_title': offer.title,
                'offer_type': offer.offer_type
            })
        else:
            return Response(
                {'error': 'Order amount does not meet minimum requirements'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def stats(self, request):
        """Get offer statistics for admin"""
        total_offers = Offer.objects.count()
        active_offers = Offer.objects.filter(status='active').count()
        expired_offers = Offer.objects.filter(status='expired').count()
        draft_offers = Offer.objects.filter(status='draft').count()
        
        # Get most used offers
        popular_offers = Offer.objects.filter(usage_count__gt=0).order_by('-usage_count')[:5]
        
        return Response({
            'total_offers': total_offers,
            'active_offers': active_offers,
            'expired_offers': expired_offers,
            'draft_offers': draft_offers,
            'popular_offers': OfferSerializer(popular_offers, many=True).data
        })
