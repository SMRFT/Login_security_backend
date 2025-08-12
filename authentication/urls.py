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
]
