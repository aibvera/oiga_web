import { request } from './client'
import { URLS } from './urls'

export const obtenerCompras = () => request(URLS.compras.lista)

export const pagar = (cantidades) =>
  request(URLS.compras.pagar, { method: 'POST', body: { cantidades } })
