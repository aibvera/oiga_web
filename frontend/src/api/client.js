import { API_BASE_URL, URLS } from './urls'

export class ApiError extends Error {
  constructor(status, data) {
    super(data?.error ?? `Error ${status}`)
    this.status = status
    this.data = data
  }
}

function leerCookie(nombre) {
  const fila = document.cookie.split('; ').find((c) => c.startsWith(`${nombre}=`))
  return fila ? decodeURIComponent(fila.split('=')[1]) : null
}

// Django rota el token CSRF al hacer login, por eso se lee de la cookie en cada petición.
async function tokenCsrf() {
  const token = leerCookie('csrftoken')
  if (token) return token
  return (await request(URLS.usuarios.csrf)).csrftoken
}

const SERVIDOR_CAIDO = { error: 'El servidor no está respondiendo. Inténtalo más tarde.' }

export async function request(path, { method = 'GET', body } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET') headers['X-CSRFToken'] = await tokenCsrf()

  let res
  try {
    res = await fetch(API_BASE_URL + path, {
      method,
      headers,
      credentials: 'include',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    // Sin conexión con el servidor (sin proxy, p. ej. en producción)
    throw new ApiError(0, SERVIDOR_CAIDO)
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null)
  // 5xx sin JSON: el proxy de Vite (o un gateway) no pudo llegar a Django
  if (res.status >= 500 && !data) throw new ApiError(res.status, SERVIDOR_CAIDO)
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}
