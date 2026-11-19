"""Pruebas de las pantallas móviles (una por historia de usuario)."""
from datetime import date

from django.test import TestCase
from django.urls import reverse

from inventario_movil import servicios
from inventario_movil.models import Articulo, Bodega, Movimiento, Stock


class VistasMovilTest(TestCase):
    def setUp(self):
        self.bodega = Bodega.objects.create(nombre='Bucaramanga')
        self.articulo = Articulo.objects.create(
            categoria='Simulacro', referencia='Saber 11', grado=11, stock_minimo=10)

    def _datos(self, **cambios):
        datos = {'articulo': self.articulo.pk, 'bodega': self.bodega.pk, 'cantidad': 8,
                 'fecha': date.today().isoformat(), 'observaciones': 'Prueba'}
        datos.update(cambios)
        return datos

    # HU-01
    def test_pantalla_incluye_viewport_para_celular(self):
        respuesta = self.client.get(reverse('inventario_movil:existencias'))
        self.assertContains(respuesta, 'name="viewport"')
        self.assertContains(respuesta, 'Simulacro Saber 11')

    def test_busqueda_sin_resultados_muestra_mensaje(self):
        respuesta = self.client.get(reverse('inventario_movil:existencias'), {'q': 'zzz'})
        self.assertContains(respuesta, "No hay artículos")

    def test_parametro_bodega_invalido_no_rompe_la_pagina(self):
        respuesta = self.client.get(reverse('inventario_movil:existencias'),
                                    {'bodega': "1 OR 1=1"})
        self.assertEqual(respuesta.status_code, 200)

    def test_filtro_bajo_minimo_marca_alerta(self):
        servicios.registrar_entrada(articulo=self.articulo, bodega=self.bodega,
                                    cantidad=3, fecha=date.today())
        respuesta = self.client.get(reverse('inventario_movil:existencias'), {'bajo': '1'})
        self.assertContains(respuesta, "Bajo mínimo")

    # HU-02
    def test_entrada_valida_actualiza_stock_y_redirige_al_kardex(self):
        respuesta = self.client.post(reverse('inventario_movil:entrada'), self._datos())
        self.assertRedirects(respuesta, reverse('inventario_movil:kardex',
                                                args=[self.articulo.pk]))
        self.assertEqual(Stock.objects.get().cantidad, 8)

    def test_entrada_con_cantidad_invalida_no_guarda(self):
        respuesta = self.client.post(reverse('inventario_movil:entrada'),
                                     self._datos(cantidad=0))
        self.assertContains(respuesta, "mayor que cero")
        self.assertEqual(Movimiento.objects.count(), 0)

    # HU-03
    def test_salida_con_stock_suficiente(self):
        servicios.registrar_entrada(articulo=self.articulo, bodega=self.bodega,
                                    cantidad=20, fecha=date.today())
        self.client.post(reverse('inventario_movil:salida'), self._datos(cantidad=5))
        self.assertEqual(Stock.objects.get().cantidad, 15)

    def test_salida_sin_stock_muestra_error_y_no_guarda(self):
        respuesta = self.client.post(reverse('inventario_movil:salida'), self._datos())
        self.assertContains(respuesta, "Stock insuficiente")
        self.assertEqual(Movimiento.objects.count(), 0)

    # HU-04
    def test_kardex_lista_movimientos_con_saldo(self):
        servicios.registrar_entrada(articulo=self.articulo, bodega=self.bodega,
                                    cantidad=20, fecha=date.today())
        respuesta = self.client.get(reverse('inventario_movil:kardex',
                                            args=[self.articulo.pk]))
        self.assertContains(respuesta, "Entrada +20")
        self.assertContains(respuesta, "Saldo")

    def test_kardex_de_articulo_inexistente_da_404(self):
        respuesta = self.client.get(reverse('inventario_movil:kardex', args=[9999]))
        self.assertEqual(respuesta.status_code, 404)

    # HU-05
    def test_crear_articulo_valido(self):
        respuesta = self.client.post(reverse('inventario_movil:articulo_nuevo'), {
            'categoria': 'Cartilla', 'referencia': 'Pensar', 'grado': 3, 'stock_minimo': 5})
        self.assertRedirects(respuesta, reverse('inventario_movil:existencias'))
        self.assertTrue(Articulo.objects.filter(categoria='Cartilla').exists())

    def test_crear_articulo_con_caracteres_especiales_muestra_error(self):
        respuesta = self.client.post(reverse('inventario_movil:articulo_nuevo'), {
            'categoria': '<b>x</b>', 'referencia': 'Pensar', 'grado': 3, 'stock_minimo': 5})
        self.assertContains(respuesta, "solo admite letras")

    def test_articulo_duplicado_no_se_crea(self):
        self.client.post(reverse('inventario_movil:articulo_nuevo'), {
            'categoria': 'Simulacro', 'referencia': 'Saber 11', 'grado': 11,
            'stock_minimo': 1})
        self.assertEqual(Articulo.objects.count(), 1)

    # PWA y seguridad
    def test_manifest_y_service_worker(self):
        manifiesto = self.client.get(reverse('inventario_movil:manifest')).json()
        self.assertEqual(manifiesto['display'], 'standalone')
        trabajador = self.client.get(reverse('inventario_movil:sw'))
        self.assertEqual(trabajador['Content-Type'], 'application/javascript')

    def test_metodo_no_permitido_en_existencias(self):
        respuesta = self.client.post(reverse('inventario_movil:existencias'))
        self.assertEqual(respuesta.status_code, 405)

    def test_post_sin_csrf_es_rechazado(self):
        from django.test import Client
        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.post(reverse('inventario_movil:entrada'), self._datos())
        self.assertEqual(respuesta.status_code, 403)
