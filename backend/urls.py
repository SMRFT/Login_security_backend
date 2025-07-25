from django.contrib import admin
from django.urls import path,include
urlpatterns = [
    path('admin/', admin.site.urls),
    path("",include('authentication.urls')),
    path("_b_a_c_k_e_n_d/Security/",include('authentication.urls'))
]
