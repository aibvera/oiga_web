from django.urls import path

from . import views

app_name = 'compras'

urlpatterns = [
    path('', views.mis_compras, name='mis_compras'),
    path('pagar/', views.pagar, name='pagar'),
]
