import re

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from google.auth.exceptions import TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from config.utils import json_invalido, leer_json, no_autenticado

from .forms import PerfilForm, RegistroForm

Usuario = get_user_model()


# =============================================================================
# Helpers
# =============================================================================

def errores_form(form):
    """{'campo': ['mensaje', ...]} listo para JSON."""
    return {
        campo: [error['message'] for error in lista]
        for campo, lista in form.errors.get_json_data().items()
    }


def usuario_a_dict(usuario):
    return {
        'id': usuario.id,
        'username': usuario.username,
        'email': usuario.email,
        'first_name': usuario.first_name,
        'last_name': usuario.last_name,
        'telefono': usuario.telefono,
        'direccion': usuario.direccion,
        'perfil_completo': usuario.perfil_completo,
    }


def username_desde_email(email):
    """Parte local del email como username, con sufijo si ya existe: ana, ana2, ana3..."""
    # Solo los caracteres que acepta el validador de username de Django
    base = re.sub(r'[^\w.@+-]', '', email.split('@')[0])[:140] or 'usuario'
    username, n = base, 1
    while Usuario.objects.filter(username=username).exists():
        n += 1
        username = f'{base}{n}'
    return username


def crear_usuario_google(info):
    usuario = Usuario(
        username=username_desde_email(info['email']),
        email=info['email'].lower(),
        first_name=info.get('given_name', '')[:150],
        last_name=info.get('family_name', '')[:150],
        google_sub=info['sub'],
    )
    usuario.set_unusable_password()  # solo puede entrar con Google
    usuario.save()
    return usuario


# =============================================================================
# Endpoints
# =============================================================================

@require_GET
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'csrftoken': get_token(request)})


@require_POST
def registro(request):
    datos = leer_json(request)
    if datos is None:
        return json_invalido()

    form = RegistroForm(datos)
    if not form.is_valid():
        return JsonResponse({'errores': errores_form(form)}, status=400)

    usuario = form.save()  # hashea la contraseña
    login(request, usuario)
    return JsonResponse(usuario_a_dict(usuario), status=201)


@require_POST
def iniciar_sesion(request):
    datos = leer_json(request)
    if datos is None:
        return json_invalido()

    identificador = str(datos.get('identificador', '')).strip()

    # Si escribió un email, buscamos su username
    if '@' in identificador:
        encontrado = Usuario.objects.filter(email__iexact=identificador).first()
        identificador = encontrado.username if encontrado else ''

    form = AuthenticationForm(request, data={
        'username': identificador,
        'password': datos.get('password', ''),
    })
    if not form.is_valid():
        # Mismo mensaje siempre: no revelar si el usuario existe
        return JsonResponse({'error': 'Credenciales inválidas.'}, status=401)

    usuario = form.get_user()
    login(request, usuario)
    return JsonResponse(usuario_a_dict(usuario))


@require_POST
def iniciar_sesion_google(request):
    """
    Botón "Continuar con Google": si la cuenta de Google ya tiene usuario, solo inicia sesión;
    si no, lo crea (201). No se vincula con cuentas ya registradas con contraseña.
    Body: {"credential": "<ID token que devuelve el botón de Google>"}.
    """
    # Sin client id, google-auth no comprobaría para qué app se emitió el token
    if not settings.GOOGLE_CLIENT_ID:
        return JsonResponse({'error': 'El inicio de sesión con Google no está disponible.'}, status=503)

    datos = leer_json(request)
    if datos is None:
        return json_invalido()

    try:
        info = id_token.verify_oauth2_token(
            str(datos.get('credential', '')),
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,  # tolera relojes ligeramente desfasados
        )
    except ValueError:
        return JsonResponse({'error': 'No se pudo validar tu cuenta de Google.'}, status=401)
    except TransportError:
        return JsonResponse({'error': 'No se pudo contactar con Google. Inténtalo de nuevo.'}, status=503)

    if not info.get('email_verified'):
        return JsonResponse({'error': 'Tu email de Google no está verificado.'}, status=401)

    usuario = Usuario.objects.filter(google_sub=info['sub']).first()
    nuevo = usuario is None
    if nuevo:
        if Usuario.objects.filter(email__iexact=info['email']).exists():
            return JsonResponse(
                {'error': 'Ya existe una cuenta con este email. Inicia sesión con tu contraseña.'},
                status=409,
            )
        usuario = crear_usuario_google(info)

    if not usuario.is_active:
        return JsonResponse({'error': 'Esta cuenta está desactivada.'}, status=403)

    login(request, usuario)
    return JsonResponse({**usuario_a_dict(usuario), 'nuevo': nuevo}, status=201 if nuevo else 200)


@require_POST
def cerrar_sesion(request):
    if not request.user.is_authenticated:
        return no_autenticado()
    logout(request)
    return HttpResponse(status=204)


@require_GET
def me(request):
    if not request.user.is_authenticated:
        return no_autenticado()
    return JsonResponse(usuario_a_dict(request.user))


@require_http_methods(['PATCH'])
def actualizar_perfil(request):
    """
    Para completar el perfil de un usuario con teléfono y dirección.
    Body: {"telefono": "...", "direccion": "..."}.
    Los campos que no se manden se conservan.
    """
    if not request.user.is_authenticated:
        return no_autenticado()

    datos = leer_json(request)
    if datos is None:
        return json_invalido()

    actuales = model_to_dict(request.user, fields=PerfilForm.Meta.fields)
    form = PerfilForm(actuales | datos, instance=request.user)
    if not form.is_valid():
        return JsonResponse({'errores': errores_form(form)}, status=400)

    usuario = form.save()
    return JsonResponse(usuario_a_dict(usuario))
