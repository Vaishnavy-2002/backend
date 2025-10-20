from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    POSSessionViewSet, QuickSaleViewSet, CustomerViewSet, 
    DailySalesViewSet, POSDashboardViewSet
)

router = DefaultRouter()
router.register(r'sessions', POSSessionViewSet, basename='pos-session')
router.register(r'sales', QuickSaleViewSet, basename='quick-sale')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'daily-sales', DailySalesViewSet, basename='daily-sales')
router.register(r'dashboard', POSDashboardViewSet, basename='pos-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
