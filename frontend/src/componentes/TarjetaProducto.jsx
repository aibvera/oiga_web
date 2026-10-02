import { useNavigate } from 'react-router'
import { aCentimos, soles } from '../precio'
import BotonAnadir from './BotonAnadir'

export default function TarjetaProducto({ producto }) {
  const navigate = useNavigate()
  const { slug, nombre, inspirado_en, descripcion, precio } = producto

  return (
    <article className="caja tarjeta">
      <h3>{nombre}</h3>
      {inspirado_en && <p className="secundario">Inspirado en: {inspirado_en}</p>}
      <p>{descripcion}</p>
      <p className="precio">{soles(aCentimos(precio))}</p>
      <div className="acciones">
        <button onClick={() => navigate(`/producto/${slug}`)}>Saber más</button>
        <BotonAnadir slug={slug} />
      </div>
    </article>
  )
}
