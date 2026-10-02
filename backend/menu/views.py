from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Categoria, Producto


# =============================================================================
# Helpers
# =============================================================================

def categoria_a_dict(categoria):
    return {
        'id': categoria.id,
        'slug': categoria.slug,
        'nombre': categoria.nombre,
        'descripcion': categoria.descripcion,
    }


def producto_a_dict(producto):
    return {
        'id': producto.id,
        'slug': producto.slug,
        'nombre': producto.nombre,
        'inspirado_en': producto.inspirado_en,
        'descripcion': producto.descripcion,
        'ingredientes': [i.strip() for i in producto.ingredientes.split(',') if i.strip()],
        'precio': str(producto.precio),  # "24.90": string para no perder precisión
    }


# =============================================================================
# Endpoints
# =============================================================================

@require_GET
def menu(request):
    """Menú completo: categorías activas con sus productos."""
    categorias = Categoria.objects.filter(activa=True).prefetch_related('productos')
    return JsonResponse({
        'categorias': [
            {**categoria_a_dict(c), 'productos': [producto_a_dict(p) for p in c.productos.all()]}
            for c in categorias
        ],
    })


@require_GET
def detalle_producto(request, slug):
    producto = (
        Producto.objects.select_related('categoria')
        .filter(slug=slug, categoria__activa=True)
        .first()
    )
    if producto is None:
        return JsonResponse({'error': 'Producto no encontrado.'}, status=404)
    return JsonResponse({**producto_a_dict(producto), 'categoria': categoria_a_dict(producto.categoria)})
