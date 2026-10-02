from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Compra(models.Model):
    # PROTECT: un usuario con compras no se puede borrar, el registro se conserva.
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='compras')

    # Soles (PEN). Lo calcula el servidor con los precios de la BD, nunca el front.
    total = models.DecimalField(max_digits=9, decimal_places=2)

    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada']
        verbose_name = 'compra'
        verbose_name_plural = 'compras'

    def __str__(self):
        return f'Compra #{self.id} de {self.usuario}'


class LineaCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='lineas')

    # SET_NULL: si el producto se borra en el admin, la línea sigue existiendo.
    producto = models.ForeignKey('menu.Producto', on_delete=models.SET_NULL, null=True, related_name='+')

    # Copias del momento de la compra: la carta puede cambiar después.
    nombre = models.CharField(max_length=100)
    precio_unitario = models.DecimalField(max_digits=7, decimal_places=2)

    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['id']
        verbose_name = 'línea de compra'
        verbose_name_plural = 'líneas de compra'
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gte=1), name='compras_linea_cantidad_minima'),
        ]

    def __str__(self):
        return f'{self.cantidad} × {self.nombre}'

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad
