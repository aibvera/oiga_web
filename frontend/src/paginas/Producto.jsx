import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { obtenerProducto } from '../api/menu'
import BotonAnadir from '../componentes/BotonAnadir'
import { aCentimos, soles } from '../precio'

export default function Producto() {
  const { slug } = useParams()
  const [producto, setProducto] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    obtenerProducto(slug)
      .then(setProducto)
      .catch((err) => setError(err.message))
  }, [slug])

  if (error) {
    return (
      <p className="error">
        {error} <Link to="/">Volver al menú</Link>
      </p>
    )
  }
  if (!producto) return <p>Cargando…</p>

  const { nombre, categoria, inspirado_en, descripcion, ingredientes, precio } = producto

  return (
    <article className="caja">
      <p className="secundario">{categoria.nombre}</p>
      <h2>{nombre}</h2>
      {inspirado_en && <p className="secundario">Inspirado en: {inspirado_en}</p>}
      <p>{descripcion}</p>
      {ingredientes.length > 0 && (
        <div>
          <h3>Ingredientes</h3>
          <ul>
            {ingredientes.map((ingrediente) => (
              <li key={ingrediente}>{ingrediente}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="precio">{soles(aCentimos(precio))}</p>
      <div className="acciones">
        <BotonAnadir slug={slug} />
      </div>
      <Link to="/">← Volver al menú</Link>
    </article>
  )
}
