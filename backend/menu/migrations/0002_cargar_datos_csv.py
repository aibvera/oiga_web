from django.db import migrations

from menu.carga import cargar_menu


def cargar_datos(apps, schema_editor):
    # Primera puesta en marcha: carga menu/data/*.csv. Solo crea lo que falta.
    cargar_menu(apps.get_model('menu', 'Categoria'), apps.get_model('menu', 'Producto'))


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        # Al revertir no se borra nada: los datos pueden haber cambiado desde el admin.
        migrations.RunPython(cargar_datos, migrations.RunPython.noop),
    ]
