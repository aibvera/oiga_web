import io
import tempfile
from decimal import Decimal
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from .carga import CARPETA_DATOS, ErrorCarga, cargar_menu
from .models import Categoria, Producto

CABECERA_PRODUCTOS = 'slug,categoria,nombre,precio\n'


class CargaMenuTests(TestCase):
    # La migración 0002 ya cargó menu/data/*.csv en la BD de test.

    def carpeta_con(self, productos, categorias='slug,nombre\npostres,Postres\n', encoding='utf-8'):
        carpeta = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (carpeta / 'categorias.csv').write_text(categorias, encoding=encoding)
        (carpeta / 'productos.csv').write_text(productos, encoding=encoding)
        return carpeta

    def test_migracion_cargo_los_csv(self):
        self.assertEqual(Categoria.objects.count(), 4)
        self.assertTrue(Producto.objects.filter(slug='ceviche-de-champinones').exists())

    def test_cargar_dos_veces_no_duplica(self):
        antes = Producto.objects.count()
        resumen = cargar_menu(Categoria, Producto)
        self.assertEqual(resumen['productos'].creados, 0)
        self.assertEqual(Producto.objects.count(), antes)

    def test_sin_actualizar_no_toca_lo_existente(self):
        carpeta = self.carpeta_con(CABECERA_PRODUCTOS + 'picarones,postres,Picarones,99.00\n')
        cargar_menu(Categoria, Producto, carpeta=carpeta)
        self.assertEqual(Producto.objects.get(slug='picarones').precio, Decimal('16.90'))

    def test_actualizar_sobrescribe(self):
        carpeta = self.carpeta_con(CABECERA_PRODUCTOS + 'picarones,postres,Picarones,99.00\n')
        resumen = cargar_menu(Categoria, Producto, actualizar=True, carpeta=carpeta)
        self.assertEqual(resumen['productos'].actualizados, 1)
        self.assertEqual(Producto.objects.get(slug='picarones').precio, Decimal('99.00'))

    def test_un_error_no_guarda_nada(self):
        carpeta = self.carpeta_con(
            CABECERA_PRODUCTOS
            + 'nuevo-postre,postres,Nuevo postre,10.00\n'
            + 'precio-malo,postres,Precio malo,abc\n'
            + 'sin-categoria,no-existe,Sin categoría,10.00\n'
        )
        with self.assertRaises(ErrorCarga) as ctx:
            cargar_menu(Categoria, Producto, carpeta=carpeta)
        self.assertEqual(len(ctx.exception.errores), 2)
        self.assertFalse(Producto.objects.filter(slug='nuevo-postre').exists())

    def test_formato_excel_en_espanol(self):
        # Excel en español: separador ';', coma decimal y BOM.
        carpeta = self.carpeta_con(
            'slug;categoria;nombre;precio\nturron;postres;Turrón;14,50\n',
            categorias='slug;nombre\npostres;Postres\n',
            encoding='utf-8-sig',
        )
        cargar_menu(Categoria, Producto, carpeta=carpeta)
        self.assertEqual(Producto.objects.get(slug='turron').precio, Decimal('14.50'))

    def test_comando_simular_no_guarda(self):
        carpeta = self.carpeta_con(CABECERA_PRODUCTOS + 'nuevo-postre,postres,Nuevo postre,10.00\n')
        call_command('cargar_menu', simular=True, carpeta=carpeta, stdout=io.StringIO())
        self.assertFalse(Producto.objects.filter(slug='nuevo-postre').exists())

    def test_csv_del_repo_son_validos(self):
        resumen = cargar_menu(Categoria, Producto, actualizar=True, simular=True, carpeta=CARPETA_DATOS)
        self.assertEqual(resumen['avisos'], [])
