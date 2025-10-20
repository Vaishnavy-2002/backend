from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SeasonalEventViewSet

router = DefaultRouter()
router.register(r'events', SeasonalEventViewSet, basename='seasonal-event')

app_name = 'seasonal_trends'

urlpatterns = [
    path('', include(router.urls)),
]
