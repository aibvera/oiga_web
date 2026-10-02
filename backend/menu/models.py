from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    orden = models.PositiveSmallIntegerField(default=0, help_text='Posición en el menú (menor = primero).')
    activa = models.BooleanField(default=True, help_text='Si se desmarca, la categoría no aparece en el menú.')

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    inspirado_en = models.CharField(
        max_length=100, blank=True,
        help_text='Plato tradicional que versiona, p. ej. "Ceviche de pescado".',
    )
    descripcion = models.TextField(blank=True)
    ingredientes = models.TextField(blank=True, help_text='Separados por comas.')
    orden = models.PositiveSmallIntegerField(default=0, help_text='Posición dentro de su categoría.')

    # Soles (PEN). Decimal, nunca float, para dinero.
    precio = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'producto'
        verbose_name_plural = 'productos'
        constraints = [
            # El validador avisa en el admin; la constraint protege la BD.
            models.CheckConstraint(condition=models.Q(precio__gte=0), name='menu_producto_precio_no_negativo'),
        ]

    def __str__(self):
        return self.nombre
    