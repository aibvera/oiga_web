import { useEffect, useEffectEvent, useRef } from 'react'

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

// El script de Google se descarga una sola vez, aunque el botón se monte varias veces
let scriptGoogle = null

function cargarScriptGoogle() {
  scriptGoogle ??= new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.onload = resolve
    script.onerror = () => {
      scriptGoogle = null // se reintenta la próxima vez que se monte el botón
      script.remove()
      reject()
    }
    document.head.append(script)
  })
  return scriptGoogle
}

// Botón oficial de Google (Google Identity Services). Al elegir cuenta llama a
// onCredencial(token); el backend valida ese token y crea la cuenta o inicia sesión.
export default function BotonGoogle({ onCredencial, onError }) {
  const contenedor = useRef(null)
  const alRecibir = useEffectEvent(onCredencial)
  const alFallar = useEffectEvent(onError)

  useEffect(() => {
    if (!CLIENT_ID) return
    let montado = true
    cargarScriptGoogle()
      .then(() => {
        if (!montado) return
        google.accounts.id.initialize({
          client_id: CLIENT_ID,
          callback: ({ credential }) => alRecibir(credential),
        })
        google.accounts.id.renderButton(contenedor.current, {
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          locale: 'es',
        })
      })
      .catch(() => montado && alFallar('No se pudo cargar el botón de Google.'))
    return () => {
      montado = false
    }
  }, [])

  // Sin client id configurado (ver .env.example) no se muestra nada
  if (!CLIENT_ID) return null
  return <div ref={contenedor} />
}
