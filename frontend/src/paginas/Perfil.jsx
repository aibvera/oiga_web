import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router'
import * as auth from '../api/auth'
import { useSesion } from '../sesion'

// Fijados al registrarse (o por Google): aquí solo se muestran
const CAMPOS_FIJOS = [
  { name: 'username', label: 'Usuario' },
  { name: 'email', label: 'Email' },
  { name: 'first_name', label: 'Nombre' },
  { name: 'last_name', label: 'Apellido' },
]

// Los que acepta PATCH /api/usuarios/perfil/
const CAMPOS_EDITABLES = [
  { name: 'telefono', label: 'Teléfono', type: 'tel' },
  { name: 'direccion', label: 'Dirección' },
]

export default function Perfil() {
  const { usuario, setUsuario } = useSesion()
  // state viene del login o del carrito: { volverA: '/carrito', aviso: '...' }
  const { state } = useLocation()
  const navigate = useNavigate()
  const [errores, setErrores] = useState({})
  const [guardando, setGuardando] = useState(false)
  const [guardado, setGuardado] = useState(false)

  if (!usuario) {
    return (
      <Navigate
        to="/login"
        state={{ volverA: '/perfil', aviso: 'Inicia sesión para ver tu perfil.' }}
        replace
      />
    )
  }

  async function guardar(e) {
    e.preventDefault()
    setErrores({})
    setGuardado(false)
    setGuardando(true)
    try {
      setUsuario(await auth.actualizarPerfil(Object.fromEntries(new FormData(e.target))))
      // Si se vino a completar el perfil (p. ej. desde el carrito), se vuelve allí
      if (state?.volverA) navigate(state.volverA)
      else setGuardado(true)
    } catch (err) {
      // 401: la sesión caducó en el servidor. Sin usuario, la página manda al login
      if (err.status === 401) setUsuario(null)
      else setErrores(err.data?.errores ?? { __all__: [err.message] })
    } finally {
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={guardar}>
      <h2>Mi perfil</h2>
      {state?.aviso && !usuario.perfil_completo && <p className="aviso">{state.aviso}</p>}
      {CAMPOS_FIJOS.map(({ name, label }) => (
        <label key={name}>
          {label}
          <input defaultValue={usuario[name]} disabled />
        </label>
      ))}
      {CAMPOS_EDITABLES.map(({ name, label, type = 'text' }) => (
        <label key={name}>
          {label}
          <input name={name} type={type} defaultValue={usuario[name]} />
          {errores[name]?.map((msg) => (
            <span key={msg} className="error">{msg}</span>
          ))}
        </label>
      ))}
      {errores.__all__?.map((msg) => (
        <p key={msg} className="error">{msg}</p>
      ))}
      {guardado && <p className="exito">Datos guardados.</p>}
      <button disabled={guardando}>{guardando ? 'Guardando…' : 'Guardar'}</button>
    </form>
  )
}
