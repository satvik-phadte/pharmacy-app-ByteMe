from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Web routes
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('homepage/', views.homepage_view, name='homepage'),
    
    # Pharmacy routes
    path('pharmacy/location/', views.pharmacy_location_view, name='pharmacy_location'),
    path('pharmacy/inventory/', views.inventory_list_view, name='inventory_list'),
    path('pharmacy/inventory/add/', views.inventory_add_view, name='inventory_add'),
    path('pharmacy/inventory/bulk-upload/', views.bulk_medicine_upload_view, name='bulk_medicine_upload'),
    path('pharmacy/inventory/<int:pk>/edit/', views.inventory_edit_view, name='inventory_edit'),
    path('pharmacy/inventory/<int:pk>/delete/', views.inventory_delete_view, name='inventory_delete'),
    
    # Customer routes
    path('customer/location/', views.customer_location_view, name='customer_location'),
    path('customer/search/', views.medicine_search_view, name='medicine_search'),
    path('customer/reminders/', views.reminders_view, name='reminders'),
    path('customer/reminders/<int:pk>/mark-taken/', views.reminder_mark_taken_today, name='reminder_mark_taken'),
    
    # API routes (no CORS)
    path('api/login/', views.api_login, name='api_login'),
    path('api/signup/', views.api_signup, name='api_signup'),
]
