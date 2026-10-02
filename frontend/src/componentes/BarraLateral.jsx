import { useEffect } from 'react'
import { NavLink } from 'react-router'
import { useCarrito } from '../carrito'
import { useSesion } from '../sesion'

export default function BarraLateral({ abierta, onCerrar }) {
  const { usuario, cerrarSesion } = useSesion()
  const { totalUnidades } = useCarrito()

  // Esc cierra la barra
  useEffect(() => {
    if (!abierta) return
    const alPulsar = (e) => e.key === 'Escape' && onCerrar()
    window.addEventListener('keydown', alPulsar)
    return () => window.removeEventListener('keydown', alPulsar)
  }, [abierta, onCerrar])

  const enlaces = [
    ['/', 'Menú'],
    ['/carrito', `Carrito (${totalUnidades})`],
    ...(usuario
      ? [['/mis-compras', 'Mis compras'], ['/perfil', 'Mi perfil']]
      : [['/login', 'Iniciar sesión'], ['/registro', 'Registrarse']]),
  ]

  return (
    <>
      {abierta && <div className="fondo" onClick={onCerrar} />}
      <nav className={abierta ? 'barra-lateral abierta' : 'barra-lateral'} inert={!abierta}>
        <button onClick={onCerrar} aria-label="Cerrar menú">✕</button>
        {enlaces.map(([ruta, texto]) => (
          <NavLink key={ruta} to={ruta} end onClick={onCerrar}>
            {texto}
          </NavLink>
        ))}
        {usuario && (
          <>
            <p>
              Hola, <strong>{usuario.username}</strong>
            </p>
            <button onClick={() => cerrarSesion().then(onCerrar)}>Cerrar sesión</button>
          </>
        )}
      </nav>
    </>
  )
}
