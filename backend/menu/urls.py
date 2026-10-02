from django.urls import path

from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.menu, name='menu'),
    path('productos/<slug:slug>/', views.detalle_producto, name='detalle_producto'),
]
