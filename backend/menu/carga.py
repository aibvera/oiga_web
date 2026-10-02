"""
Carga la carta desde los CSV de menu/data/ sin duplicar nada.

Cada fila se identifica por su `slug`:
- si el slug no existe en la BD, se crea;
- si ya existe, no se toca (salvo con actualizar=True, que lo sobrescribe con el CSV).

Todo va en una sola transacción: si alguna fila tiene un error, no se guarda ninguna.

Formato de los CSV:
- Cabecera con los nombres de los campos del modelo. `id`, `creado` y `actualizado` se ignoran.
- En productos.csv, la columna `categoria` lleva el slug de la categoría.
- Separador `,` o `;` (Excel en español usa `;`). Codificación UTF-8 (con o sin BOM).
- Booleanos: si/no, 1/0, true/false. Decimales: 24.90 o 24,90.
- Una celda vacía usa el valor por defecto del campo.

Se usa desde el comando `cargar_menu` y desde la migración 0002_cargar_datos_csv,
que recibe los modelos históricos (por eso los modelos se pasan como parámetro).
"""
import csv
from dataclasses import dataclass
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models, transaction

CARPETA_DATOS = Path(__file__).resolve().parent / 'data'

# Campos que se rellenan solos: no se leen del CSV.
CAMPOS_AUTOMATICOS = {'id', 'creado', 'actualizado'}

VERDADEROS = {'si', 'sí', '1', 'true', 'x'}
FALSOS = {'no', '0', 'false'}


class ErrorCarga(Exception):
    def __init__(self, errores):
        super().__init__('\n'.join(errores))
        self.errores = errores


@dataclass
class Contador:
    creados: int = 0
    actualizados: int = 0
    sin_tocar: int = 0


# =============================================================================
# Lectura y conversión
# =============================================================================

def leer_csv(ruta):
    """Devuelve (columnas, [(numero_de_fila, fila), ...]) saltando filas vacías."""
    with open(ruta, encoding='utf-8-sig', newline='') as archivo:
        cabecera = archivo.readline()
        archivo.seek(0)
        separador = ';' if cabecera.count(';') > cabecera.count(',') else ','
        lector = csv.DictReader(archivo, delimiter=separador)
        filas = [
            (numero, fila)
            for numero, fila in enumerate(lector, start=2)
            if any((valor or '').strip() for valor in fila.values() if isinstance(valor, str))
        ]
    columnas = [c.strip() for c in lector.fieldnames or []]
    return columnas, filas


def convertir(campo, texto, relaciones):
    """Convierte el texto de una celda al tipo Python del campo."""
    texto = texto.strip()

    if texto == '':
        if isinstance(campo, (models.CharField, models.TextField)):
            return ''
        return campo.get_default() if campo.has_default() else None

    if campo.is_relation:
        try:
            return relaciones[campo.name][texto]
        except KeyError:
            raise ValidationError(f'no existe "{texto}".')

    if isinstance(campo, models.BooleanField):
        if texto.lower() in VERDADEROS:
            return True
        if texto.lower() in FALSOS:
            return False
        raise ValidationError(f'"{texto}" no es si/no.')

    if isinstance(campo, models.DecimalField) and '.' not in texto:
        texto = texto.replace(',', '.')

    return campo.to_python(texto)


# =============================================================================
# Carga
# =============================================================================

def cargar_tabla(modelo, ruta, actualizar, errores, avisos, relaciones=None):
    contador = Contador()
    relaciones = relaciones or {}

    if not ruta.exists():
        errores.append(f'No existe el archivo {ruta}.')
        return contador

    columnas, filas = leer_csv(ruta)
    campos = {
        campo.name: campo
        for campo in modelo._meta.concrete_fields
        if campo.name not in CAMPOS_AUTOMATICOS
    }

    if 'slug' not in columnas:
        errores.append(f'{ruta.name}: falta la columna "slug".')
        return contador

    ignoradas = [c for c in columnas if c not in campos]
    if ignoradas:
        avisos.append(f'{ruta.name}: columnas ignoradas {ignoradas}.')

    slugs_vistos = set()

    for numero, fila in filas:
        donde = f'{ruta.name}, fila {numero}'
        fila = {k.strip() if k is not None else None: v for k, v in fila.items()}

        if None in fila:
            errores.append(f'{donde}: tiene más celdas que columnas en la cabecera.')
            continue

        slug = (fila.get('slug') or '').strip()
        if not slug:
            errores.append(f'{donde}: falta el slug.')
            continue
        if slug in slugs_vistos:
            errores.append(f'{donde}: el slug "{slug}" está repetido en el CSV.')
            continue
        slugs_vistos.add(slug)

        objeto = modelo.objects.filter(slug=slug).first()
        if objeto is not None and not actualizar:
            contador.sin_tocar += 1
            continue

        valores, fallos = {}, []
        for columna in columnas:
            if columna not in campos or columna == 'slug':
                continue
            try:
                valores[columna] = convertir(campos[columna], fila.get(columna) or '', relaciones)
            except ValidationError as error:
                fallos.append(f'{columna}: {" ".join(error.messages)}')
        if fallos:
            errores.append(f'{donde}: {"; ".join(fallos)}')
            continue

        es_nuevo = objeto is None
        if es_nuevo:
            objeto = modelo(slug=slug)
        elif all(getattr(objeto, campo) == valor for campo, valor in valores.items()):
            contador.sin_tocar += 1
            continue

        for campo, valor in valores.items():
            setattr(objeto, campo, valor)

        try:
            objeto.full_clean()
        except ValidationError as error:
            detalle = '; '.join(f'{campo}: {" ".join(msgs)}' for campo, msgs in error.message_dict.items())
            errores.append(f'{donde}: {detalle}')
            continue

        objeto.save()
        if es_nuevo:
            contador.creados += 1
        else:
            contador.actualizados += 1

    return contador


def cargar_menu(Categoria, Producto, actualizar=False, simular=False, carpeta=CARPETA_DATOS):
    """
    Carga categorias.csv y productos.csv. Lanza ErrorCarga (sin guardar nada) si hay errores.
    Devuelve {'categorias': Contador, 'productos': Contador, 'avisos': [...]}.
    """
    carpeta = Path(carpeta)
    errores, avisos = [], []

    with transaction.atomic():
        categorias = cargar_tabla(Categoria, carpeta / 'categorias.csv', actualizar, errores, avisos)

        por_slug = {c.slug: c for c in Categoria.objects.all()}
        productos = cargar_tabla(
            Producto, carpeta / 'productos.csv', actualizar, errores, avisos,
            relaciones={'categoria': por_slug},
        )

        if errores:
            raise ErrorCarga(errores)
        if simular:
            transaction.set_rollback(True)

    return {'categorias': categorias, 'productos': productos, 'avisos': avisos}
