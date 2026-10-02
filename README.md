# Oiga

Web de pedidos de un restaurante de cocina peruana 100 % vegetal: carta por categorías, carrito, registro/login (con contraseña o Google) e historial de compras. El pago se simula.

**Stack:** Django 6 + PostgreSQL 17 (API JSON) · React 19 + Vite (SPA) · Render.

## Estructura

```
backend/            Django (API)
  config/           settings, urls, middleware, helpers JSON
  usuarios/         modelo Usuario, registro, login, Google, perfil
  menu/             Categoria, Producto; data/*.csv se carga en la migración 0002
  compras/          Compra, LineaCompra, pagar
frontend/           React + Vite
  src/api/          cliente HTTP; urls.js es el único sitio con las rutas de la API
  src/paginas/      una por ruta de React Router
  src/componentes/
docker-compose.yml  Postgres de desarrollo
render.yaml         Blueprint de Render
.env.example        variables del backend (el front tiene frontend/.env.example)
```

## Desarrollo

1. `docker compose up -d` (Postgres en `127.0.0.1:5432`) y copia `.env.example` a `.env`.
2. Backend: en `backend/`, crea `.venv`, `pip install -r requirements.txt`, `python manage.py migrate` y `python manage.py runserver`.
3. Front: en `frontend/`, `npm install` y `npm run dev` → http://localhost:5173.

Vite reenvía `/api/*` a Django, así que front y API comparten origen. Antes de subir a `main` deben pasar `python manage.py test` y `npm run build`.

## Contrato back ↔ front

- Todo es JSON bajo `/api/`. La sesión va en cookie (`credentials: 'include'`).
- Toda petición que no sea GET lleva el header `X-CSRFToken` con el valor de la cookie `csrftoken` (si no existe, se pide a `/api/usuarios/csrf/`).
- Errores: `{"error": "..."}`, o `{"errores": {"campo": ["..."]}}` en formularios. Sin sesión → `401`.
- Dinero como string (`"24.90"`), nunca como float. Soles (PEN).

| Método | Ruta | Body / respuesta |
|---|---|---|
| GET | `/api/usuarios/csrf/` | `{csrftoken}` |
| POST | `/api/usuarios/registro/` | `{username, email, first_name, last_name, telefono, direccion, password1, password2}` → usuario (201) |
| POST | `/api/usuarios/login/` | `{identificador, password}` (usuario o email) → usuario |
| POST | `/api/usuarios/google/` | `{credential}` → usuario + `nuevo` (201 si se crea) |
| POST | `/api/usuarios/logout/` | → 204 |
| GET | `/api/usuarios/me/` | usuario |
| PATCH | `/api/usuarios/perfil/` | `{telefono?, direccion?}` → usuario |
| GET | `/api/menu/` | `{categorias: [{…, productos: [...]}]}` |
| GET | `/api/menu/productos/<slug>/` | producto + `categoria` |
| GET | `/api/compras/` | `{compras: [...]}` del usuario |
| POST | `/api/compras/pagar/` | `{cantidades: {slug: n}}` (1–99) → compra (201) |

**Usuario:** `id, username, email, first_name, last_name, telefono, direccion, perfil_completo`.
Para pagar hace falta `perfil_completo` (si falta, la respuesta trae `perfil_incompleto: true`). Los precios y el total los calcula siempre el servidor.

## Despliegue en Render (plan free)

`render.yaml` crea tres recursos: la BD `oiga-db`, la API `oiga-api` (gunicorn) y el front estático `oiga`. El front reenvía `/api/*` a la API, de modo que para el navegador todo es el mismo dominio.

1. Sube el repo a GitHub (comprueba que `.env` y `frontend/.env.local` no se suben).
2. En Render: **New → Blueprint** → el repo. Rellena las variables `sync: false`:
   - `FRONTEND_URL`: URL del front, p. ej. `https://oiga.onrender.com`.
   - `GOOGLE_CLIENT_ID` y `VITE_GOOGLE_CLIENT_ID`: el mismo Client ID.
   - `DJANGO_SUPERUSER_USERNAME`, `_PASSWORD`, `_EMAIL`, `_TELEFONO`, `_DIRECCION`: superusuario para `/admin`, creado en el primer build. Ninguno puede ir vacío.
3. Si Render asigna otras URLs, corrige `FRONTEND_URL` en el panel o el `destination` del rewrite en `render.yaml`.
4. En Google Cloud Console, añade la URL del front a *Orígenes autorizados de JavaScript*.

Cada push o merge a `main` redespliega automáticamente el servicio cuya carpeta (`backend/` o `frontend/`) cambió. Las migraciones corren en el build.

**Límites del plan free:** la API se duerme tras 15 min sin tráfico (la primera petición tarda ~1 min), la BD caduca a los 30 días y no hay Shell. Al pasar a pago, cambia `plan:` en `render.yaml` y mueve `migrate` y `createsuperuser` a `preDeployCommand`.
