from django.contrib import admin

from .models import Compra, LineaCompra


class SoloLectura:
    """Las compras solo se crean desde la API: en el admin se consultan, no se tocan."""

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class LineaCompraInline(SoloLectura, admin.TabularInline):
    model = LineaCompra
    fields = ('producto', 'nombre', 'precio_unitario', 'cantidad', 'subtotal')
    readonly_fields = fields


@admin.register(Compra)
class CompraAdmin(SoloLectura, admin.ModelAdmin):
    list_display = ('id', 'usuario', 'total', 'creada')
    list_filter = ('creada',)
    date_hierarchy = 'creada'
    search_fields = ('usuario__username', 'usuario__email')
    list_select_related = ('usuario',)
    inlines = [LineaCompraInline]
