import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router'
import { obtenerCompras } from '../api/compras'
import { aCentimos, soles } from '../precio'
import { useSesion } from '../sesion'

const formatoFecha = new Intl.DateTimeFormat('es-PE', { dateStyle: 'long', timeStyle: 'short' })

export default function MisCompras() {
  const { usuario, setUsuario } = useSesion()
  const [compras, setCompras] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!usuario) return
    obtenerCompras()
      .then((datos) => setCompras(datos.compras))
      .catch((err) => {
        // 401: la sesión caducó en el servidor. Sin usuario, la página manda al login
        if (err.status === 401) setUsuario(null)
        else setError(err.message)
      })
  }, [usuario])

  if (!usuario) {
    return (
      <Navigate
        to="/login"
        state={{ volverA: '/mis-compras', aviso: 'Inicia sesión para ver tus compras.' }}
        replace
      />
    )
  }
  if (error) return <p className="error">{error}</p>
  if (!compras) return <p>Cargando compras…</p>

  return (
    <div className="historial">
      <h2>Mis compras</h2>
      {compras.length === 0 ? (
        <div className="caja">
          <p>
            Aún no has hecho ninguna compra. <Link to="/">Ver el menú</Link>
          </p>
        </div>
      ) : (
        compras.map(({ id, creada, total, lineas }) => (
          <article key={id} className="caja">
            <h3>Compra #{id}</h3>
            <p className="secundario">{formatoFecha.format(new Date(creada))}</p>
            <table>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Cantidad</th>
                  <th className="num">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {/* Las líneas no traen id, pero su orden nunca cambia: sirve el índice */}
                {lineas.map(({ nombre, precio_unitario, cantidad, subtotal }, i) => (
                  <tr key={i}>
                    <td>
                      {nombre}
                      <br />
                      <span className="secundario">{soles(aCentimos(precio_unitario))} c/u</span>
                    </td>
                    <td>{cantidad}</td>
                    <td className="num">{soles(aCentimos(subtotal))}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th colSpan="2">Total</th>
                  <th className="num">{soles(aCentimos(total))}</th>
                </tr>
              </tfoot>
            </table>
          </article>
        ))
      )}
    </div>
  )
}
