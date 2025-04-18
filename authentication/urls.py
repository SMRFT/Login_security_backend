from django.urls import path, include
from . import views 
urlpatterns = [
    path('_b_a_c_k_e_n_d/Security/login/', views.login_view, name='login'),
]
