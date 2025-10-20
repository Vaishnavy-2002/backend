from rest_framework import serializers
from .models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    cake_image_url = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Feedback
        fields = ['id', 'user', 'user_info', 'order', 'message', 'rating', 'cake_image', 'cake_image_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_cake_image_url(self, obj):
        if obj.cake_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cake_image.url)
            return obj.cake_image.url
        return None
    
    def get_user_info(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'full_name': obj.user.get_full_name(),
                'display_name': self._get_user_display_name(obj.user),
                'is_registered': True
            }
        return {
            'id': None,
            'username': None,
            'email': None,
            'first_name': None,
            'last_name': None,
            'full_name': None,
            'display_name': 'Anonymous',
            'is_registered': False
        }
    
    def _get_user_display_name(self, user):
        """
        Get display name for user - full name, username, or email prefix
        """
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        elif user.first_name:
            return user.first_name
        elif user.username:
            return user.username
        else:
            return user.email.split('@')[0] if user.email else "User"