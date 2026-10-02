"""Helpers comunes a las vistas JSON de todas las apps."""
import json

from django.http import JsonResponse


def leer_json(request):
    """Devuelve el body como dict, o None si no es JSON válido."""
    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return datos if isinstance(datos, dict) else None


def json_invalido():
    return JsonResponse({'error': 'JSON inválido.'}, status=400)


def no_autenticado():
    return JsonResponse({'error': 'No has iniciado sesión.'}, status=401)
