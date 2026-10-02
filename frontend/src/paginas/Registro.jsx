import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router'
import * as auth from '../api/auth'
import { useSesion } from '../sesion'

const CAMPOS_REGISTRO = [
  { name: 'username', label: 'Usuario' },
  { name: 'email', label: 'Email', type: 'email' },
  { name: 'first_name', label: 'Nombre' },
  { name: 'last_name', label: 'Apellido' },
  { name: 'telefono', label: 'Teléfono' },
  { name: 'direccion', label: 'Dirección' },
  { name: 'password1', label: 'Contraseña', type: 'password' },
  { name: 'password2', label: 'Repetir contraseña', type: 'password' },
]

export default function Registro() {
  const { usuario, setUsuario } = useSesion()
  const { state } = useLocation()
  const [errores, setErrores] = useState({})

  // Django inicia sesión al registrarse: se vuelve a donde se venía
  if (usuario) return <Navigate to={state?.volverA ?? '/'} replace />

  async function enviar(e) {
    e.preventDefault()
    setErrores({})
    try {
      setUsuario(await auth.registro(Object.fromEntries(new FormData(e.target))))
    } catch (err) {
      setErrores(err.data?.errores ?? { __all__: [err.message] })
    }
  }

  return (
    <form onSubmit={enviar}>
      <h2>Registro</h2>
      {state?.aviso && <p className="aviso">{state.aviso}</p>}
      {CAMPOS_REGISTRO.map(({ name, label, type = 'text' }) => (
        <label key={name}>
          {label}
          <input name={name} type={type} />
          {errores[name]?.map((msg) => (
            <span key={msg} className="error">{msg}</span>
          ))}
        </label>
      ))}
      {errores.__all__?.map((msg) => (
        <p key={msg} className="error">{msg}</p>
      ))}
      <button>Crear cuenta</button>
      <p>
        ¿Ya tienes cuenta?{' '}
        <Link to="/login" state={state}>
          Inicia sesión
        </Link>
      </p>
    </form>
  )
}
