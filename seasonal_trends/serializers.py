from rest_framework import serializers
from .models import SeasonalEvent


class SeasonalEventSerializer(serializers.ModelSerializer):
    """Serializer for SeasonalEvent model"""
    
    formatted_date = serializers.ReadOnlyField()
    month_name = serializers.SerializerMethodField()
    sales_color = serializers.ReadOnlyField()
    sales_bg_color = serializers.ReadOnlyField()
    
    class Meta:
        model = SeasonalEvent
        fields = [
            'id', 'name', 'description', 'month', 'day', 'year',
            'sales_level', 'products', 'expected_revenue', 'growth_rate',
            'icon', 'color', 'is_active', 'formatted_date', 'month_name',
            'sales_color', 'sales_bg_color', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_month_name(self, obj):
        """Get month name from month number"""
        return obj.get_month_name()
    
    def validate(self, data):
        """Validate the data"""
        # Check if the date is valid
        try:
            from datetime import date
            date(data.get('year', 2025), data.get('month'), data.get('day'))
        except ValueError:
            raise serializers.ValidationError("Invalid date provided")
        
        return data


class SeasonalEventListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing seasonal events"""
    
    formatted_date = serializers.ReadOnlyField()
    month_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SeasonalEvent
        fields = [
            'id', 'name', 'month', 'day', 'year', 'sales_level',
            'products', 'expected_revenue', 'growth_rate', 'icon',
            'color', 'formatted_date', 'month_name', 'is_active'
        ]
    
    def get_month_name(self, obj):
        """Get month name from month number"""
        return obj.get_month_name()
