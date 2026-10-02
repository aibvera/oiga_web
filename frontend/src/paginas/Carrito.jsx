import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import * as compras from '../api/compras'
import { obtenerMenu } from '../api/menu'
import { CANTIDAD_MAXIMA, useCarrito } from '../carrito'
import { aCentimos, soles } from '../precio'
import { useSesion } from '../sesion'

export default function Carrito() {
  const { usuario, setUsuario } = useSesion()
  const { cantidades, anadir, quitarUno, eliminar, vaciar } = useCarrito()
  const navigate = useNavigate()
  const [productos, setProductos] = useState(null) // { slug: producto }
  const [error, setError] = useState(null)
  const [pagando, setPagando] = useState(false)
  const [errorPago, setErrorPago] = useState(null)
  const [compra, setCompra] = useState(null) // la recién pagada, para el mensaje de éxito

  useEffect(() => {
    obtenerMenu()
      .then(({ categorias }) => {
        const todos = categorias.flatMap((c) => c.productos)
        setProductos(Object.fromEntries(todos.map((p) => [p.slug, p])))
      })
      .catch((err) => setError(err.message))
  }, [])

  // Si un producto se borró o desactivó en el admin, sale del carrito
  useEffect(() => {
    if (!productos) return
    Object.keys(cantidades)
      .filter((slug) => !productos[slug])
      .forEach(eliminar)
  }, [productos])

  function pedirLogin() {
    navigate('/login', {
      state: { volverA: '/carrito', aviso: 'Inicia sesión para pagar. Tu carrito se mantiene.' },
    })
  }

  // Quien entró con Google puede no haber dado aún teléfono y dirección
  function pedirPerfil() {
    navigate('/perfil', {
      state: {
        volverA: '/carrito',
        aviso: 'Completa tu teléfono y dirección para pagar. Tu carrito se mantiene.',
      },
    })
  }

  async function pagar() {
    if (!usuario) return pedirLogin()
    if (!usuario.perfil_completo) return pedirPerfil()

    setErrorPago(null)
    setPagando(true)
    try {
      // Solo se mandan las cantidades: el servidor calcula el total con los precios de la BD
      setCompra(await compras.pagar(cantidades))
      vaciar()
    } catch (err) {
      if (err.status === 401) {
        // La sesión caducó en el servidor: se vuelve a pedir login, el carrito se mantiene
        setUsuario(null)
        pedirLogin()
      } else {
        // Si algo se borró o desactivó en el admin mientras tanto, también sale del carrito
        err.data?.no_disponibles?.forEach(eliminar)
        setErrorPago(err.message)
      }
    } finally {
      setPagando(false)
    }
  }

  if (error) return <p className="error">{error}</p>
  if (!productos) return <p>Cargando carrito…</p>

  const lineas = Object.entries(cantidades)
    .filter(([slug]) => productos[slug])
    .map(([slug, cantidad]) => {
      const producto = productos[slug]
      return { ...producto, cantidad, subtotal: aCentimos(producto.precio) * cantidad }
    })
  const total = lineas.reduce((suma, linea) => suma + linea.subtotal, 0)

  return (
    <div className="caja">
      <h2>Carrito</h2>
      {compra && (
        <p className="exito">
          ¡Pago realizado! Compra #{compra.id} por {soles(aCentimos(compra.total))}.{' '}
          <Link to="/mis-compras">Ver mis compras</Link>
        </p>
      )}
      {errorPago && <p className="error">{errorPago}</p>}
      {lineas.length === 0 ? (
        <p>
          Tu carrito está vacío. <Link to="/">Ver el menú</Link>
        </p>
      ) : (
        <>
          <table>
            <thead>
              <tr>
                <th>Producto</th>
                <th>Cantidad</th>
                <th className="num">Subtotal</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {lineas.map(({ slug, nombre, precio, cantidad, subtotal }) => (
                <tr key={slug}>
                  <td>
                    {nombre}
                    <br />
                    <span className="secundario">{soles(aCentimos(precio))} c/u</span>
                  </td>
                  <td className="cantidad">
                    <button onClick={() => quitarUno(slug)} aria-label={`Quitar un ${nombre}`}>
                      −
                    </button>
                    {cantidad}
                    <button
                      onClick={() => anadir(slug)}
                      disabled={cantidad >= CANTIDAD_MAXIMA}
                      aria-label={`Añadir un ${nombre}`}
                    >
                      +
                    </button>
                  </td>
                  <td className="num">{soles(subtotal)}</td>
                  <td className="num">
                    <button onClick={() => eliminar(slug)} aria-label={`Quitar ${nombre} del carrito`}>
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <th colSpan="2">Total</th>
                <th className="num">{soles(total)}</th>
                <th />
              </tr>
            </tfoot>
          </table>
          <button onClick={pagar} disabled={pagando}>
            {pagando ? 'Pagando…' : 'PAGAR'}
          </button>
        </>
      )}
    </div>
  )
}
