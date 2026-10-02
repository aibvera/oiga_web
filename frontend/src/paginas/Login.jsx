import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router'
import * as auth from '../api/auth'
import BotonGoogle from '../componentes/BotonGoogle'
import { useSesion } from '../sesion'

export default function Login() {
  const { usuario, setUsuario } = useSesion()
  // state viene del carrito: { volverA: '/carrito', aviso: '...' }
  const { state } = useLocation()
  const [error, setError] = useState(null)

  if (usuario) {
    // Quien entra por primera vez con Google aún no tiene teléfono ni dirección
    if (!usuario.perfil_completo) {
      return (
        <Navigate
          to="/perfil"
          state={{
            volverA: state?.volverA,
            aviso: 'Completa tu teléfono y dirección para poder hacer pedidos.',
          }}
          replace
        />
      )
    }
    // Con sesión iniciada se vuelve a donde se venía (p. ej. el carrito, que sigue intacto)
    return <Navigate to={state?.volverA ?? '/'} replace />
  }

  async function enviar(e) {
    e.preventDefault()
    const { identificador, password } = Object.fromEntries(new FormData(e.target))
    setError(null)
    try {
      setUsuario(await auth.login(identificador, password))
    } catch (err) {
      setError(err.message)
    }
  }

  async function entrarConGoogle(credential) {
    setError(null)
    try {
      setUsuario(await auth.loginGoogle(credential))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form onSubmit={enviar}>
      <h2>Iniciar sesión</h2>
      {state?.aviso && <p className="aviso">{state.aviso}</p>}
      <label>
        Usuario o email
        <input name="identificador" required />
      </label>
      <label>
        Contraseña
        <input name="password" type="password" required />
      </label>
      {error && <p className="error">{error}</p>}
      <button>Entrar</button>
      <p className="secundario">o</p>
      <BotonGoogle onCredencial={entrarConGoogle} onError={setError} />
      <p>
        ¿No tienes cuenta?{' '}
        <Link to="/registro" state={state}>
          Regístrate
        </Link>
      </p>
    </form>
  )
}
