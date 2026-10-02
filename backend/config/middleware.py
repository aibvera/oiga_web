from django.conf import settings


class DesactivarCsrfEnDevMiddleware:
    """
    SOLO DESARROLLO: desactiva la comprobación CSRF para poder probar la API
    desde Postman sin enviar el header X-CSRFToken.

    Debe ir ANTES de 'django.middleware.csrf.CsrfViewMiddleware'.
    En producción (DJANGO_DEBUG=False) no hace nada: el CSRF se exige siempre.
    Lo comprueba usuarios.tests.CsrfTests.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG:
            request._dont_enforce_csrf_checks = True
        return self.get_response(request)
