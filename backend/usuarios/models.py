from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)

    # Opcionales en la BD: quien entra con Google no los tiene hasta completar su perfil.
    # El registro normal (RegistroForm) los sigue exigiendo.
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)

    # Id estable de la cuenta de Google ("sub" del token). None = cuenta sin Google.
    google_sub = models.CharField(max_length=255, unique=True, null=True, blank=True)

    REQUIRED_FIELDS = ['email', 'telefono', 'direccion']

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return self.username

    @property
    def perfil_completo(self):
        """Sin teléfono y dirección no se puede hacer un pedido."""
        return bool(self.telefono and self.direccion)
