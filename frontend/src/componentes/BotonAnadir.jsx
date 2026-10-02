import { CANTIDAD_MAXIMA, useCarrito } from '../carrito'

// Funciona con o sin sesión: el carrito es local hasta el momento de pagar.
export default function BotonAnadir({ slug }) {
  const { cantidades, anadir } = useCarrito()
  const cantidad = cantidades[slug]

  return (
    <>
      <button onClick={() => anadir(slug)} disabled={cantidad >= CANTIDAD_MAXIMA}>
        Añadir al carrito
      </button>
      {cantidad > 0 && <span className="secundario">{cantidad} en el carrito</span>}
    </>
  )
}
