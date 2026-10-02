import { useEffect, useState } from 'react'
import { obtenerMenu } from '../api/menu'
import TarjetaProducto from '../componentes/TarjetaProducto'

export default function Menu() {
  const [categorias, setCategorias] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    obtenerMenu()
      .then((datos) => setCategorias(datos.categorias))
      .catch((err) => setError(err.message))
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!categorias) return <p>Cargando menú…</p>

  return categorias.map((categoria) => (
    <div key={categoria.slug} className="categoria">
      <h2>{categoria.nombre}</h2>
      {categoria.descripcion && <p className="secundario">{categoria.descripcion}</p>}
      <div className="rejilla">
        {categoria.productos.map((producto) => (
          <TarjetaProducto key={producto.slug} producto={producto} />
        ))}
      </div>
    </div>
  ))
}
