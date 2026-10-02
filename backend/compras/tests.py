from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Categoria, Producto

from .models import Compra

Usuario = get_user_model()


class PagarTests(TestCase):
    # La migración menu/0002 ya cargó los productos de menu/data/*.csv en la BD de test.

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='ana', password='clave-segura-123', email='ana@example.com',
            telefono='999999999', direccion='Av. Siempre Viva 123',
        )
        self.client.force_login(self.usuario)

    def pagar(self, cuerpo):
        return self.client.post(reverse('compras:pagar'), cuerpo, content_type='application/json')

    def test_sin_sesion_no_registra(self):
        self.client.logout()
        respuesta = self.pagar({'cantidades': {'picarones': 1}})
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(Compra.objects.count(), 0)

    def test_pago_valido_registra_la_compra(self):
        ceviche = Producto.objects.get(slug='ceviche-de-champinones')
        picarones = Producto.objects.get(slug='picarones')

        respuesta = self.pagar({'cantidades': {'ceviche-de-champinones': 2, 'picarones': 1}})

        self.assertEqual(respuesta.status_code, 201)
        compra = Compra.objects.get()
        self.assertEqual(compra.usuario, self.usuario)
        self.assertEqual(compra.total, ceviche.precio * 2 + picarones.precio)
        self.assertEqual(compra.lineas.count(), 2)
        self.assertEqual(respuesta.json()['total'], str(compra.total))

    def test_precio_del_cliente_se_ignora(self):
        precio_real = Producto.objects.get(slug='picarones').precio
        self.pagar({'cantidades': {'picarones': 1}, 'total': '0.01', 'precio': '0.01'})
        self.assertEqual(Compra.objects.get().total, precio_real)

    def test_carrito_vacio(self):
        for cuerpo in ({'cantidades': {}}, {}, {'cantidades': ['picarones']}):
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual(self.pagar(cuerpo).status_code, 400)
        self.assertEqual(Compra.objects.count(), 0)

    def test_json_invalido(self):
        respuesta = self.client.post(reverse('compras:pagar'), 'no es json', content_type='application/json')
        self.assertEqual(respuesta.status_code, 400)

    def test_cantidades_invalidas(self):
        # 100 supera el tope; 2**63 antes tumbaba el servidor (no cabe en un entero de la BD)
        for cantidad in (0, -1, '2', 1.5, True, None, 100, 2**63):
            with self.subTest(cantidad=cantidad):
                self.assertEqual(self.pagar({'cantidades': {'picarones': cantidad}}).status_code, 400)
        self.assertEqual(Compra.objects.count(), 0)

    def test_cantidad_maxima_permitida(self):
        self.assertEqual(self.pagar({'cantidades': {'picarones': 99}}).status_code, 201)

    def test_producto_inexistente_no_guarda_nada(self):
        respuesta = self.pagar({'cantidades': {'picarones': 1, 'no-existe': 1}})
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()['no_disponibles'], ['no-existe'])
        self.assertEqual(Compra.objects.count(), 0)

    def test_perfil_incompleto_no_puede_pagar(self):
        # Caso de quien entró con Google y aún no dio teléfono ni dirección
        Usuario.objects.filter(pk=self.usuario.pk).update(telefono='', direccion='')

        respuesta = self.pagar({'cantidades': {'picarones': 1}})

        self.assertEqual(respuesta.status_code, 400)
        self.assertTrue(respuesta.json()['perfil_incompleto'])
        self.assertEqual(Compra.objects.count(), 0)

    def test_categoria_inactiva_no_se_puede_comprar(self):
        Categoria.objects.filter(productos__slug='picarones').update(activa=False)
        self.assertEqual(self.pagar({'cantidades': {'picarones': 1}}).status_code, 400)

    def test_cambio_de_precio_no_altera_la_compra(self):
        self.pagar({'cantidades': {'picarones': 1}})
        precio_original = Compra.objects.get().total
        Producto.objects.filter(slug='picarones').update(precio=Decimal('99.00'))

        linea = Compra.objects.get().lineas.get()
        self.assertEqual(linea.precio_unitario, precio_original)

    def test_borrar_producto_conserva_la_linea(self):
        self.pagar({'cantidades': {'picarones': 1}})
        Producto.objects.get(slug='picarones').delete()

        linea = Compra.objects.get().lineas.get()
        self.assertIsNone(linea.producto)
        self.assertEqual(linea.nombre, 'Picarones')


class MisComprasTests(TestCase):

    def crear_usuario(self, username):
        return Usuario.objects.create_user(
            username=username, password='clave-segura-123', email=f'{username}@example.com',
            telefono='999999999', direccion='Av. Siempre Viva 123',
        )

    def test_sin_sesion(self):
        self.assertEqual(self.client.get(reverse('compras:mis_compras')).status_code, 401)

    def test_solo_devuelve_las_compras_propias(self):
        ana, beto = self.crear_usuario('ana'), self.crear_usuario('beto')
        url_pagar = reverse('compras:pagar')

        self.client.force_login(beto)
        self.client.post(url_pagar, {'cantidades': {'picarones': 3}}, content_type='application/json')

        self.client.force_login(ana)
        self.client.post(url_pagar, {'cantidades': {'picarones': 1}}, content_type='application/json')

        compras = self.client.get(reverse('compras:mis_compras')).json()['compras']
        self.assertEqual(len(compras), 1)
        self.assertEqual(compras[0]['lineas'][0]['cantidad'], 1)
