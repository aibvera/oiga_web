from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/usuarios/', include('usuarios.urls')),
    path('api/menu/', include('menu.urls')),
    path('api/compras/', include('compras.urls')),
]
