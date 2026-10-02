from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from menu.carga import CARPETA_DATOS, ErrorCarga, cargar_menu
from menu.models import Categoria, Producto


class Command(BaseCommand):
    help = 'Carga categorías y productos desde menu/data/*.csv sin duplicar (identifica cada fila por su slug).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--actualizar', action='store_true',
            help='Sobrescribe con los valores del CSV las filas que ya existen en la BD.',
        )
        parser.add_argument(
            '--simular', action='store_true',
            help='Muestra lo que haría sin guardar nada.',
        )
        parser.add_argument(
            '--carpeta', type=Path, default=CARPETA_DATOS,
            help='Carpeta con categorias.csv y productos.csv (por defecto menu/data/).',
        )

    def handle(self, *args, **options):
        try:
            resumen = cargar_menu(
                Categoria, Producto,
                actualizar=options['actualizar'],
                simular=options['simular'],
                carpeta=options['carpeta'],
            )
        except ErrorCarga as error:
            lineas = '\n'.join(f'  - {e}' for e in error.errores)
            raise CommandError(f'No se guardó nada. Corrige estos errores:\n{lineas}')

        for aviso in resumen['avisos']:
            self.stdout.write(self.style.WARNING(aviso))

        for tabla in ('categorias', 'productos'):
            c = resumen[tabla]
            self.stdout.write(f'{tabla}: {c.creados} creados, {c.actualizados} actualizados, {c.sin_tocar} sin tocar')

        if options['simular']:
            self.stdout.write(self.style.WARNING('Simulación: no se guardó nada.'))
        else:
            self.stdout.write(self.style.SUCCESS('Carga completada.'))
