from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from google.auth.exceptions import TransportError

Usuario = get_user_model()


def info_google(**cambios):
    """Lo que devuelve verify_oauth2_token para un token válido."""
    return {
        'sub': '1234567890',
        'email': 'Ana.Perez@gmail.com',
        'email_verified': True,
        'given_name': 'Ana',
        'family_name': 'Pérez',
        **cambios,
    }


@override_settings(GOOGLE_CLIENT_ID='client-id-de-prueba.apps.googleusercontent.com')
class LoginGoogleTests(TestCase):
    # Nunca se llama a Google: se simula la verificación del token.

    def entrar(self, info=None, efecto=None, cuerpo=None):
        with patch('usuarios.views.id_token.verify_oauth2_token', return_value=info, side_effect=efecto) as verificar:
            respuesta = self.client.post(
                reverse('usuarios:google'),
                cuerpo if cuerpo is not None else {'credential': 'token'},
                content_type='application/json',
            )
        self.verificar = verificar
        return respuesta

    def hay_sesion(self):
        return self.client.get(reverse('usuarios:me')).status_code == 200

    def test_usuario_nuevo_crea_la_cuenta(self):
        respuesta = self.entrar(info_google())

        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertTrue(datos['nuevo'])
        self.assertFalse(datos['perfil_completo'])

        usuario = Usuario.objects.get()
        self.assertEqual(usuario.google_sub, '1234567890')
        self.assertEqual(usuario.email, 'ana.perez@gmail.com')
        self.assertEqual(usuario.username, 'Ana.Perez')
        self.assertEqual((usuario.first_name, usuario.last_name), ('Ana', 'Pérez'))
        self.assertFalse(usuario.has_usable_password())
        self.assertTrue(self.hay_sesion())

    def test_se_verifica_contra_nuestro_client_id(self):
        self.entrar(info_google())
        token, _, audiencia = self.verificar.call_args.args
        self.assertEqual(token, 'token')
        self.assertEqual(audiencia, 'client-id-de-prueba.apps.googleusercontent.com')

    def test_usuario_existente_solo_inicia_sesion(self):
        self.entrar(info_google())
        self.client.logout()

        respuesta = self.entrar(info_google())

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()['nuevo'])
        self.assertEqual(Usuario.objects.count(), 1)
        self.assertTrue(self.hay_sesion())

    def test_cambio_de_email_en_google_sigue_siendo_la_misma_cuenta(self):
        self.entrar(info_google())
        self.client.logout()

        respuesta = self.entrar(info_google(email='otro@gmail.com'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 1)

    def test_email_ya_registrado_con_contrasena_no_se_vincula(self):
        Usuario.objects.create_user(
            username='ana', password='clave-segura-123', email='ana.perez@gmail.com',
            telefono='999999999', direccion='Av. Siempre Viva 123',
        )

        respuesta = self.entrar(info_google())

        self.assertEqual(respuesta.status_code, 409)
        self.assertIsNone(Usuario.objects.get().google_sub)
        self.assertFalse(self.hay_sesion())

    def test_username_repetido_lleva_sufijo(self):
        Usuario.objects.create_user(username='Ana.Perez', password='clave-segura-123', email='ana@example.com')
        self.entrar(info_google())
        self.assertTrue(Usuario.objects.filter(username='Ana.Perez2', google_sub='1234567890').exists())

    def test_username_sin_caracteres_raros(self):
        self.entrar(info_google(email="o'brien!@gmail.com"))
        self.assertEqual(Usuario.objects.get().username, 'obrien')

    def test_token_invalido(self):
        respuesta = self.entrar(efecto=ValueError('Token expired'))
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(Usuario.objects.count(), 0)
        self.assertFalse(self.hay_sesion())

    def test_google_no_responde(self):
        self.assertEqual(self.entrar(efecto=TransportError('sin red')).status_code, 503)

    def test_email_no_verificado(self):
        respuesta = self.entrar(info_google(email_verified=False))
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_usuario_desactivado(self):
        self.entrar(info_google())
        self.client.logout()
        Usuario.objects.update(is_active=False)

        self.assertEqual(self.entrar(info_google()).status_code, 403)
        self.assertFalse(self.hay_sesion())

    @override_settings(GOOGLE_CLIENT_ID='')
    def test_sin_client_id_no_se_verifica_nada(self):
        respuesta = self.entrar(info_google())
        self.assertEqual(respuesta.status_code, 503)
        self.verificar.assert_not_called()

    def test_json_invalido(self):
        respuesta = self.client.post(reverse('usuarios:google'), 'no es json', content_type='application/json')
        self.assertEqual(respuesta.status_code, 400)


class PerfilTests(TestCase):

    def setUp(self):
        # Como queda alguien recién entrado con Google: sin teléfono ni dirección
        self.usuario = Usuario.objects.create_user(username='ana', email='ana@gmail.com', google_sub='123')
        self.client.force_login(self.usuario)

    def actualizar(self, cuerpo):
        return self.client.patch(reverse('usuarios:perfil'), cuerpo, content_type='application/json')

    def test_completar_perfil(self):
        respuesta = self.actualizar({'telefono': '999999999', 'direccion': 'Av. Siempre Viva 123'})

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()['perfil_completo'])
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.direccion, 'Av. Siempre Viva 123')

    def test_cambiar_un_solo_campo_conserva_el_otro(self):
        self.actualizar({'telefono': '999999999', 'direccion': 'Av. Siempre Viva 123'})
        self.actualizar({'telefono': '988888888'})

        self.usuario.refresh_from_db()
        self.assertEqual((self.usuario.telefono, self.usuario.direccion), ('988888888', 'Av. Siempre Viva 123'))

    def test_campos_vacios(self):
        respuesta = self.actualizar({'telefono': '999999999'})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('direccion', respuesta.json()['errores'])

    def test_no_cambia_otros_campos(self):
        self.actualizar({'telefono': '999999999', 'direccion': 'Av. 1', 'email': 'otro@gmail.com', 'is_staff': True})
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, 'ana@gmail.com')
        self.assertFalse(self.usuario.is_staff)

    def test_sin_sesion(self):
        self.client.logout()
        self.assertEqual(self.actualizar({'telefono': '999999999'}).status_code, 401)


class RegistroTests(TestCase):

    def test_registro_normal_sigue_exigiendo_telefono_y_direccion(self):
        respuesta = self.client.post(reverse('usuarios:registro'), {
            'username': 'ana', 'email': 'ana@example.com',
            'password1': 'clave-segura-123', 'password2': 'clave-segura-123',
        }, content_type='application/json')

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(set(respuesta.json()['errores']), {'telefono', 'direccion'})
        self.assertEqual(Usuario.objects.count(), 0)


FRONT = 'https://oiga.example.com'


@override_settings(DEBUG=False, CORS_ALLOWED_ORIGINS=[FRONT], CSRF_TRUSTED_ORIGINS=[FRONT])
class CsrfTests(TestCase):
    """Producción (DEBUG=False): el CSRF se exige siempre y solo se acepta el origen del front."""

    def setUp(self):
        # El Client normal se salta el CSRF; este lo comprueba como un navegador
        self.client = Client(enforce_csrf_checks=True)
        Usuario.objects.create_user(username='ana', email='ana@example.com', password='clave-segura-123')

    def entrar(self, **headers):
        return self.client.post(
            reverse('usuarios:login'), {'identificador': 'ana', 'password': 'clave-segura-123'},
            content_type='application/json', headers=headers,
        )

    def token(self):
        return self.client.get(reverse('usuarios:csrf')).json()['csrftoken']

    def test_sin_token_se_rechaza(self):
        self.assertEqual(self.entrar().status_code, 403)

    def test_con_token_se_acepta(self):
        self.assertEqual(self.entrar(x_csrftoken=self.token()).status_code, 200)

    def test_solo_desde_el_origen_del_front(self):
        token = self.token()
        self.assertEqual(self.entrar(x_csrftoken=token, origin='https://malo.example.com').status_code, 403)
        self.assertEqual(self.entrar(x_csrftoken=token, origin=FRONT).status_code, 200)

    def test_cors_con_cookies_solo_para_el_front(self):
        respuesta = self.client.get(reverse('usuarios:csrf'), headers={'origin': FRONT})
        self.assertEqual(respuesta.headers['Access-Control-Allow-Origin'], FRONT)
        self.assertEqual(respuesta.headers['Access-Control-Allow-Credentials'], 'true')

        respuesta = self.client.get(reverse('usuarios:csrf'), headers={'origin': 'https://malo.example.com'})
        self.assertNotIn('Access-Control-Allow-Origin', respuesta.headers)

    @override_settings(DEBUG=True)
    def test_en_dev_no_se_exige_para_poder_usar_postman(self):
        self.assertEqual(self.entrar().status_code, 200)
