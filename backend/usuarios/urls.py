from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('csrf/', views.csrf, name='csrf'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.iniciar_sesion, name='login'),
    path('google/', views.iniciar_sesion_google, name='google'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('me/', views.me, name='me'),
    path('perfil/', views.actualizar_perfil, name='perfil'),
]
