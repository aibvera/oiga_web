// Único sitio del front donde se definen las URLs de la API.
// Si cambia una ruta en Django, se cambia solo aquí.

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const URLS = {
  usuarios: {
    csrf: '/api/usuarios/csrf/',
    registro: '/api/usuarios/registro/',
    login: '/api/usuarios/login/',
    google: '/api/usuarios/google/',
    logout: '/api/usuarios/logout/',
    me: '/api/usuarios/me/',
    perfil: '/api/usuarios/perfil/',
  },
  menu: {
    lista: '/api/menu/',
    producto: (slug) => `/api/menu/productos/${slug}/`,
  },
  compras: {
    lista: '/api/compras/',
    pagar: '/api/compras/pagar/',
  },
}
