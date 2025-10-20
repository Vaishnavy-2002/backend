from django.urls import path
from . import views

app_name = 'cakes'

urlpatterns = [
    path('cakes/', views.CakeListAPIView.as_view(), name='cake_list'),
    path('cakes/<int:pk>/', views.CakeDetailAPIView.as_view(), name='cake_detail'),
    # Admin cake management
    path('admin/cakes/', views.AdminCakeListCreateAPIView.as_view(), name='admin_cake_list_create'),
    path('admin/cakes/<int:pk>/', views.AdminCakeRetrieveUpdateDestroyAPIView.as_view(), name='admin_cake_rud'),
    # Admin category management
    path('admin/categories/', views.AdminCategoryListCreateAPIView.as_view(), name='admin_category_list_create'),
    path('admin/categories/<int:pk>/', views.AdminCategoryRetrieveUpdateDestroyAPIView.as_view(), name='admin_category_rud'),
    path('categories/', views.CategoryListAPIView.as_view(), name='category_list'),
    path('customize/', views.CustomCakeCreateAPIView.as_view(), name='custom_cake_create'),
    path('cakes/<int:cake_id>/reviews/', views.cake_reviews, name='cake_reviews'),
    path('cakes/<int:cake_id>/reviews/create/', views.create_review, name='create_review'),
    path('cakes/<int:cake_id>/calculate-price/', views.calculate_customized_price, name='calculate_price'),
]
