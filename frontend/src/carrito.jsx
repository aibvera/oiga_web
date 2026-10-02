import { createContext, useContext, useEffect, useState } from 'react'

// El carrito vive en localStorage: sobrevive a recargas, al login y al logout.
// Solo guarda { slug: cantidad }; nombre y precio se leen siempre de la API.
const CLAVE = 'oiga.carrito'

// Mismo tope por producto que el backend (CANTIDAD_MAXIMA en compras/views.py)
export const CANTIDAD_MAXIMA = 99

const esCantidadValida = (n) => Number.isInteger(n) && n >= 1 && n <= CANTIDAD_MAXIMA

function leerGuardado() {
  try {
    const guardado = JSON.parse(localStorage.getItem(CLAVE))
    // Solo se conservan las cantidades válidas: lo guardado puede venir de otra versión o editado a mano
    return Object.fromEntries(Object.entries(guardado ?? {}).filter(([, n]) => esCantidadValida(n)))
  } catch {
    return {}
  }
}

const CarritoContext = createContext(null)

export function CarritoProvider({ children }) {
  const [cantidades, setCantidades] = useState(leerGuardado)

  useEffect(() => {
    localStorage.setItem(CLAVE, JSON.stringify(cantidades))
  }, [cantidades])

  function cambiar(slug, delta) {
    setCantidades((actual) => {
      const { [slug]: cantidad = 0, ...resto } = actual
      const nueva = Math.min(cantidad + delta, CANTIDAD_MAXIMA)
      return nueva > 0 ? { ...actual, [slug]: nueva } : resto
    })
  }

  const valor = {
    cantidades,
    totalUnidades: Object.values(cantidades).reduce((suma, n) => suma + n, 0),
    anadir: (slug) => cambiar(slug, 1),
    quitarUno: (slug) => cambiar(slug, -1),
    eliminar: (slug) => setCantidades(({ [slug]: _, ...resto }) => resto),
    vaciar: () => setCantidades({}),
  }

  return <CarritoContext value={valor}>{children}</CarritoContext>
}

export const useCarrito = () => useContext(CarritoContext)
