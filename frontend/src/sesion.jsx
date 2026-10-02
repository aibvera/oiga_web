import { createContext, useContext, useEffect, useState } from 'react'
import * as auth from './api/auth'

const SesionContext = createContext(null)

export function SesionProvider({ children }) {
  // undefined = comprobando sesión, null = sin sesión, objeto = usuario logueado
  const [usuario, setUsuario] = useState(undefined)

  useEffect(() => {
    auth.me().then(setUsuario).catch(() => setUsuario(null))
  }, [])

  async function cerrarSesion() {
    await auth.logout().catch(() => {})
    setUsuario(null)
  }

  return <SesionContext value={{ usuario, setUsuario, cerrarSesion }}>{children}</SesionContext>
}

export const useSesion = () => useContext(SesionContext)
