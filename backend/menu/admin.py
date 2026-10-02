from django.contrib import admin

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activa')
    list_editable = ('orden', 'activa')
    prepopulated_fields = {'slug': ('nombre',)}


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'orden')
    list_editable = ('precio', 'orden')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'inspirado_en', 'descripcion', 'ingredientes')
    list_select_related = ('categoria',)
    prepopulated_fields = {'slug': ('nombre',)}

    fieldsets = (
        (None, {'fields': ('categoria', 'nombre', 'slug', 'inspirado_en', 'descripcion', 'ingredientes')}),
        ('Precio y visibilidad', {'fields': ('precio', 'orden')}),
    )
    