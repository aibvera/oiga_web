import { useState } from 'react'
import { Link, Route, Routes } from 'react-router'
import { useCarrito } from './carrito'
import BarraLateral from './componentes/BarraLateral'
import Carrito from './paginas/Carrito'
import Login from './paginas/Login'
import Menu from './paginas/Menu'
import MisCompras from './paginas/MisCompras'
import Perfil from './paginas/Perfil'
import Producto from './paginas/Producto'
import Registro from './paginas/Registro'
import { useSesion } from './sesion'

export default function App() {
  const { usuario } = useSesion()
  const { totalUnidades } = useCarrito()
  const [barraAbierta, setBarraAbierta] = useState(false)

  if (usuario === undefined) return <main>Cargando…</main>

  return (
    <>
      <header className="cabecera">
        <button onClick={() => setBarraAbierta(true)} aria-label="Abrir menú">
          ☰
        </button>
        <Link to="/" className="marca">
          Oiga
        </Link>
        <Link to="/carrito">Carrito ({totalUnidades})</Link>
      </header>
      <BarraLateral abierta={barraAbierta} onCerrar={() => setBarraAbierta(false)} />
      <main>
        <Routes>
          <Route path="/" element={<Menu />} />
          <Route path="/producto/:slug" element={<Producto />} />
          <Route path="/carrito" element={<Carrito />} />
          <Route path="/mis-compras" element={<MisCompras />} />
          <Route path="/perfil" element={<Perfil />} />
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Registro />} />
          <Route
            path="*"
            element={
              <p>
                Página no encontrada. <Link to="/">Volver al menú</Link>
              </p>
            }
          />
        </Routes>
      </main>
    </>
  )
}
