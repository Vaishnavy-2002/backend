from django.urls import path
from . import views

urlpatterns = [
    path('dashboard-analytics/', views.dashboard_analytics, name='dashboard_analytics'),
    path('sales-analytics/', views.sales_analytics, name='sales_analytics'),
    path('seasonal-trends/', views.seasonal_trends, name='seasonal_trends'),
    path('customer-loyalty/', views.customer_loyalty, name='customer_loyalty'),
    path('best-selling-items/', views.best_selling_items_analyzer, name='best_selling_items_analyzer'),
    path('profit-analysis/', views.profit_analysis, name='profit_analysis'),
    path('promote-cake/', views.promote_cake, name='promote_cake'),
    path('send-gratitude-emails/', views.send_gratitude_emails, name='send_gratitude_emails'),
    path('create-special-offers/', views.create_special_offers, name='create_special_offers'),
]
