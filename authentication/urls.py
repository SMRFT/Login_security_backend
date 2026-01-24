from django.urls import path, include
from . import views
from .forgetpassword import forgot_password,verify_reset_token,reset_password

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('get_modules/', views.getmodules, name='getmodules'),
    path('get_data_entitlements', views.get_data_entitlements, name='get_data_entitlements'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('verify-reset-token/', verify_reset_token, name='verify_reset_token'),
    path('reset-password/', reset_password, name='reset_password'),
    path('m-dashboard-stats/', views.m_dashboard_stats),
    path('employees_birthdays_today/', views.get_todays_birthdays, name='employee-birthdays-today'),
    path('get_file/<str:file_id>', views.get_file, name='get_file'),
]
