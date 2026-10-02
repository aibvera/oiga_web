import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Variables de entorno del .env de la raíz del repo (junto a backend/ y frontend/).
# En Render no hay .env: las variables se definen en el panel (ver render.yaml).
load_dotenv(BASE_DIR.parent / '.env')


def env_lista(nombre):
    """'a, b,c/' -> ['a', 'b', 'c']. Vacía si la variable no existe."""
    return [valor.strip().rstrip('/') for valor in os.environ.get(nombre, '').split(',') if valor.strip()]


SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
DEBUG = os.environ.get('DJANGO_DEBUG', '').lower() in ('1', 'true')

# Dominios desde los que se sirve la API. Render añade el suyo en RENDER_EXTERNAL_HOSTNAME.
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', *env_lista('DJANGO_ALLOWED_HOSTS')]
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
if DEBUG:
    ALLOWED_HOSTS = ['*']  # DEV: cualquier host (p. ej. la IP local para probar desde el móvil)

# URL del front en producción, p. ej. https://oiga.onrender.com (varias separadas por comas).
# En dev no hace falta: Vite redirige /api a Django y todo es el mismo origen.
FRONTEND_URLS = env_lista('FRONTEND_URL')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros:
    'corsheaders',

    # Propias:
    'usuarios',
    'menu',
    'compras',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # antes de CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    # DEV: permite usar Postman sin token CSRF. Con DEBUG=False no hace nada.
    'config.middleware.DesactivarCsrfEnDevMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database

AUTH_USER_MODEL = 'usuarios.Usuario'

# postgres://usuario:clave@host:puerto/bd. En dev, el Postgres de docker-compose.yml (ver .env.example).
if not os.environ.get('DATABASE_URL'):
    raise ImproperlyConfigured('Falta DATABASE_URL en el .env (ver .env.example).')

DATABASES = {
    'default': dj_database_url.parse(
        os.environ['DATABASE_URL'],
        conn_max_age=600,  # reutiliza la conexión entre peticiones
        conn_health_checks=True,  # y la descarta si Postgres la cerró
    ),
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Lima'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'

# Destino de collectstatic (lo ejecuta el build de Render). Solo los usa el admin.
STATIC_ROOT = BASE_DIR / 'staticfiles'


# Email: la app aún no envía correos. En dev se imprimirían en la consola; en producción
# Django usa SMTP por defecto (configurar MAILERS con el servidor cuando haga falta).

if DEBUG:
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.console.EmailBackend',
        },
    }


# Duración de la sesión en segundos (por defecto: 2 semanas)
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 horas

# Cerrar la sesión al cerrar el navegador (por defecto: False)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Renovar el tiempo en cada petición (por defecto: False)
SESSION_SAVE_EVERY_REQUEST = False


# Front en otro origen: CORS con cookies, y CSRF acepta peticiones que vengan de él

CORS_ALLOWED_ORIGINS = FRONTEND_URLS
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = FRONTEND_URLS


# Login con Google: OAuth Client ID de Google Cloud Console. Vacío = desactivado.
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')


# =============================================================================
# Producción (DEBUG=False)
# =============================================================================

if not DEBUG:
    # Render termina el HTTPS y reenvía a Django por HTTP indicando el protocolo original en este header
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Render ya redirige HTTP -> HTTPS antes de llegar a Django; hacerlo aquí también
    # podría romper las peticiones que el front le reenvía (rewrite /api/* de render.yaml).
    SECURE_SSL_REDIRECT = False

    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 días: el navegador ya no intenta HTTP
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    # W008: ver SECURE_SSL_REDIRECT. W021 (HSTS preload): solo tiene sentido con dominio propio.
    SILENCED_SYSTEM_CHECKS = ['security.W008', 'security.W021']

    # Cookies solo por HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Si el front vive en otro dominio (p. ej. otro *.onrender.com), el navegador solo
    # manda las cookies de sesión y CSRF con SameSite=None. El token CSRF sigue exigiéndose.
    if FRONTEND_URLS:
        SESSION_COOKIE_SAMESITE = 'None'
        CSRF_COOKIE_SAMESITE = 'None'

    # Los estáticos del admin los sirve WhiteNoise (en dev lo hace runserver). Va justo tras SecurityMiddleware.
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }

    # Sin esto, con DEBUG=False los errores 500 no se imprimen en ningún sitio (Logs de Render)
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {'consola': {'class': 'logging.StreamHandler'}},
        'loggers': {'django': {'handlers': ['consola'], 'level': 'ERROR'}},
    }
