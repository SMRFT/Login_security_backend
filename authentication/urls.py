from django.urls import path

from .views import login_view
urlpatterns = [
    path('Security/login/',login_view, name='login'),
]
