from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'order', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['message', 'user__username']
    readonly_fields = ['created_at']