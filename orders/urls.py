from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderStatusHistoryViewSet, ShippingAddressViewSet, PaymentViewSet, trigger_ingredient_deduction
from .admin_dashboard import admin_dashboard_stats

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'status-history', OrderStatusHistoryViewSet, basename='order-status-history')
router.register(r'shipping-addresses', ShippingAddressViewSet, basename='shipping-address')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('admin-dashboard/', admin_dashboard_stats, name='admin-dashboard'),
    path('orders/<int:order_id>/deduct-ingredients/', trigger_ingredient_deduction, name='trigger-ingredient-deduction'),
]
