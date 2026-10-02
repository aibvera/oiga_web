import { request } from './client'
import { URLS } from './urls'

export const obtenerMenu = () => request(URLS.menu.lista)

export const obtenerProducto = (slug) => request(URLS.menu.producto(slug))
