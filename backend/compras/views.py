from django.db import transaction
from django.http import JsonResponse
from django.utils.timezone import localtime
from django.views.decorators.http import require_GET, require_POST

from config.utils import json_invalido, leer_json, no_autenticado
from menu.models import Producto

from .models import Compra, LineaCompra


# =============================================================================
# Helpers
# =============================================================================

def linea_a_dict(linea):
    return {
        'nombre': linea.nombre,
        'precio_unitario': str(linea.precio_unitario),
        'cantidad': linea.cantidad,
        'subtotal': str(linea.subtotal),
    }


def compra_a_dict(compra):
    return {
        'id': compra.id,
        'creada': localtime(compra.creada).isoformat(),
        'total': str(compra.total),
        'lineas': [linea_a_dict(l) for l in compra.lineas.all()],
    }


# Tope por producto: sin él, una cantidad enorme desborda la BD (error 500) o el total.
# El carrito del front usa el mismo tope (frontend/src/carrito.jsx).
CANTIDAD_MAXIMA = 99


def es_cantidad_valida(cantidad):
    # type() y no isinstance(): True es un int en Python y no debe colar como 1.
    return type(cantidad) is int and 1 <= cantidad <= CANTIDAD_MAXIMA


# =============================================================================
# Endpoints
# =============================================================================

@require_POST
def pagar(request):
    """
    Registra la compra del carrito. El pago se simula: llegar aquí con sesión es haber pagado.
    Body: {"cantidades": {"slug": cantidad, ...}}, el mismo formato que el carrito del front.
    """
    if not request.user.is_authenticated:
        return no_autenticado()

    # Quien entró con Google aún puede no tener a dónde ni a quién llamar para el pedido
    if not request.user.perfil_completo:
        return JsonResponse({
            'error': 'Completa tu teléfono y dirección antes de pagar.',
            'perfil_incompleto': True,
        }, status=400)

    datos = leer_json(request)
    if datos is None:
        return json_invalido()

    cantidades = datos.get('cantidades')
    if not isinstance(cantidades, dict) or not cantidades:
        return JsonResponse({'error': 'El carrito está vacío.'}, status=400)

    if not all(es_cantidad_valida(c) for c in cantidades.values()):
        return JsonResponse(
            {'error': f'Las cantidades deben ser números enteros entre 1 y {CANTIDAD_MAXIMA}.'}, status=400,
        )

    # Mismo filtro que el menú: solo productos de categorías activas
    productos = {
        p.slug: p
        for p in Producto.objects.filter(slug__in=cantidades, categoria__activa=True)
    }
    no_disponibles = [slug for slug in cantidades if slug not in productos]
    if no_disponibles:
        return JsonResponse({
            'error': 'Algunos productos ya no están disponibles.',
            'no_disponibles': no_disponibles,
        }, status=400)

    # Precios siempre de la BD: lo que mande el front se ignora
    lineas = [
        LineaCompra(producto=p, nombre=p.nombre, precio_unitario=p.precio, cantidad=cantidades[slug])
        for slug, p in productos.items()
    ]

    with transaction.atomic():
        compra = Compra.objects.create(
            usuario=request.user,
            total=sum(linea.subtotal for linea in lineas),
        )
        for linea in lineas:
            linea.compra = compra
        LineaCompra.objects.bulk_create(lineas)

    return JsonResponse(compra_a_dict(compra), status=201)


@require_GET
def mis_compras(request):
    if not request.user.is_authenticated:
        return no_autenticado()
    compras = request.user.compras.prefetch_related('lineas')
    return JsonResponse({'compras': [compra_a_dict(c) for c in compras]})
