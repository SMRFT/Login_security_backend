from django.urls import path, include
from . import views
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('get_modules/', views.getmodules, name='getmodules'),
    path('get_data_entitlements', views.get_data_entitlements, name='get_data_entitlements'),
]
