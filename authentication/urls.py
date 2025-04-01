from django.urls import path, include
from . import views 
urlpatterns = [
    path('Security/login/', views.login_view, name='login'),
]
