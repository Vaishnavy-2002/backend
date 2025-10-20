from rest_framework import serializers
from .models import Offer

class OfferSerializer(serializers.ModelSerializer):
    is_active = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    discount_display = serializers.SerializerMethodField()
    validity_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'description',
            'offer_type',
            'status',
            'discount_percentage',
            'discount_amount',
            'minimum_order_amount',
            'start_date',
            'end_date',
            'banner_image',
            'background_color',
            'text_color',
            'is_homepage_featured',
            'is_popup',
            'target_user_types',
            'usage_count',
            'max_usage',
            'is_active',
            'is_expired',
            'discount_display',
            'validity_status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['usage_count', 'created_at', 'updated_at']
    
    def get_discount_display(self, obj):
        """Get formatted discount display"""
        if obj.offer_type == 'percentage' and obj.discount_percentage:
            return f"{obj.discount_percentage}% OFF"
        elif obj.offer_type == 'fixed' and obj.discount_amount:
            return f"RS {obj.discount_amount} OFF"
        elif obj.offer_type == 'free_delivery':
            return "FREE DELIVERY"
        elif obj.offer_type == 'buy_one_get_one':
            return "BUY 1 GET 1"
        else:
            return "SPECIAL OFFER"
    
    def get_validity_status(self, obj):
        """Get validity status"""
        from django.utils import timezone
        now = timezone.now()
        
        if obj.is_expired:
            return {
                'status': 'expired',
                'message': 'Offer has expired',
                'end_date': obj.end_date
            }
        elif obj.start_date > now:
            return {
                'status': 'upcoming',
                'message': 'Offer starts soon',
                'start_date': obj.start_date
            }
        elif obj.is_active:
            return {
                'status': 'active',
                'message': 'Offer is active',
                'end_date': obj.end_date
            }
        else:
            return {
                'status': 'inactive',
                'message': 'Offer is inactive'
            }
    
    def validate(self, data):
        """Validate offer data"""
        # Validate discount fields based on offer type
        if data.get('offer_type') == 'percentage':
            if not data.get('discount_percentage'):
                raise serializers.ValidationError("Discount percentage is required for percentage offers")
            if data.get('discount_percentage') > 100:
                raise serializers.ValidationError("Discount percentage cannot exceed 100%")
        elif data.get('offer_type') == 'fixed':
            if not data.get('discount_amount'):
                raise serializers.ValidationError("Discount amount is required for fixed amount offers")
        
        # Validate date range
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        return data

class OfferCreateSerializer(OfferSerializer):
    """Serializer for creating offers"""
    class Meta(OfferSerializer.Meta):
        fields = OfferSerializer.Meta.fields + ['created_by']
    
    def create(self, validated_data):
        """Create offer with current user as creator"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class HomepageOfferSerializer(serializers.ModelSerializer):
    """Simplified serializer for homepage display"""
    discount_display = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'description',
            'offer_type',
            'discount_display',
            'banner_image',
            'background_color',
            'text_color',
            'is_popup',
            'time_remaining',
            'end_date'
        ]
    
    def get_discount_display(self, obj):
        """Get formatted discount display"""
        if obj.offer_type == 'percentage' and obj.discount_percentage:
            return f"{obj.discount_percentage}% OFF"
        elif obj.offer_type == 'fixed' and obj.discount_amount:
            return f"RS {obj.discount_amount} OFF"
        elif obj.offer_type == 'free_delivery':
            return "FREE DELIVERY"
        elif obj.offer_type == 'buy_one_get_one':
            return "BUY 1 GET 1"
        else:
            return "SPECIAL OFFER"
    
    def get_time_remaining(self, obj):
        """Get time remaining until offer expires"""
        from django.utils import timezone
        now = timezone.now()
        
        if obj.end_date > now:
            time_diff = obj.end_date - now
            days = time_diff.days
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days} days, {hours} hours"
            elif hours > 0:
                return f"{hours} hours, {minutes} minutes"
            else:
                return f"{minutes} minutes"
        else:
            return "Expired"
