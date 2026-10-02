import { request } from './client'
import { URLS } from './urls'

export const registro = (datos) => request(URLS.usuarios.registro, { method: 'POST', body: datos })

export const login = (identificador, password) =>
  request(URLS.usuarios.login, { method: 'POST', body: { identificador, password } })

// credential: el token que entrega el botón de Google. Crea la cuenta si es nueva.
export const loginGoogle = (credential) =>
  request(URLS.usuarios.google, { method: 'POST', body: { credential } })

export const logout = () => request(URLS.usuarios.logout, { method: 'POST' })

export const me = () => request(URLS.usuarios.me)

export const actualizarPerfil = (datos) =>
  request(URLS.usuarios.perfil, { method: 'PATCH', body: datos })
