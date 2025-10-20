"""
URL configuration for sweetbite_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('cakes.urls')),
    path('api/users/', include('users.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/pos/', include('pos.urls')),
    path('api/', include('feedback.urls')),
    path('api/', include('offers.urls')),
    path('api/', include('seasonal_trends.urls')),
    path('api/analytics/', include('analytics.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
