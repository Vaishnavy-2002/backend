from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierViewSet, IngredientViewSet, StockMovementViewSet,
    PurchaseOrderViewSet, RecipeViewSet
)
from .inventory_dashboard import inventory_dashboard_stats

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'stock-movements', StockMovementViewSet, basename='stock-movement')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', inventory_dashboard_stats, name='inventory-dashboard'),
]
