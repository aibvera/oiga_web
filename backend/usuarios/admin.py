from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'telefono', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'telefono', 'first_name', 'last_name')

    # Formulario de edición: añade una sección con los campos nuevos
    fieldsets = UserAdmin.fieldsets + (
        ('Datos de contacto', {'fields': ('telefono', 'direccion')}),
        ('Google', {'fields': ('google_sub',)}),
    )
    # Lo pone el login con Google; editarlo a mano rompería el acceso de esa cuenta
    readonly_fields = ('google_sub',)

    # Formulario de creación ("Añadir usuario")
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos de contacto', {'fields': ('email', 'telefono', 'direccion')}),
    )
