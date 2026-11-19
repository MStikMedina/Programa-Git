"""Pruebas de la lógica de negocio: stock, kardex y consultas."""
from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from inventario_movil import servicios
from inventario_movil.models import Articulo, Bodega, Movimiento, Stock


class ServiciosTest(TestCase):
    def setUp(self):
        self.bodega = Bodega.objects.create(nombre='Bucaramanga')
        self.otra = Bodega.objects.create(nombre='Barranquilla')
        self.articulo = Articulo.objects.create(
            categoria='Simulacro', referencia='Saber 11', grado=11, stock_minimo=10)

    def _entrada(self, cantidad, bodega=None):
        return servicios.registrar_entrada(
            articulo=self.articulo, bodega=bodega or self.bodega,
            cantidad=cantidad, fecha=date.today())

    def test_entrada_suma_stock_y_deja_kardex(self):
        movimiento = self._entrada(25)
        self.assertEqual(Stock.objects.get().cantidad, 25)
        self.assertEqual(movimiento.saldo_resultante, 25)
        self.assertEqual(movimiento.delta, 25)

    def test_salida_resta_stock(self):
        self._entrada(25)
        movimiento = servicios.registrar_salida(
            articulo=self.articulo, bodega=self.bodega, cantidad=10, fecha=date.today())
        self.assertEqual(Stock.objects.get().cantidad, 15)
        self.assertEqual(movimiento.delta, -10)

    def test_salida_mayor_al_stock_lanza_error_y_no_escribe(self):
        self._entrada(5)
        with self.assertRaises(servicios.StockInsuficiente) as contexto:
            servicios.registrar_salida(articulo=self.articulo, bodega=self.bodega,
                                       cantidad=6, fecha=date.today())
        self.assertEqual(contexto.exception.disponible, 5)
        self.assertEqual(Stock.objects.get().cantidad, 5)
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_salida_sin_existencias_falla(self):
        with self.assertRaises(servicios.StockInsuficiente):
            servicios.registrar_salida(articulo=self.articulo, bodega=self.bodega,
                                       cantidad=1, fecha=date.today())

    def test_stock_es_independiente_por_bodega(self):
        self._entrada(10)
        self._entrada(7, self.otra)
        self.assertEqual(Stock.objects.get(bodega=self.bodega).cantidad, 10)
        self.assertEqual(Stock.objects.get(bodega=self.otra).cantidad, 7)

    def test_articulo_duplicado_viola_restriccion_unica(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Articulo.objects.create(categoria='Simulacro', referencia='Saber 11', grado=11)

    def test_grado_mayor_a_11_viola_check(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Articulo.objects.create(categoria='X', referencia='Y', grado=12)

    def test_existencias_con_total_y_alerta_bajo_minimo(self):
        self._entrada(4)  # mínimo 10 → alerta
        fila = servicios.existencias_con_total()[0]
        self.assertEqual(fila['total'], 4)
        self.assertTrue(fila['bajo_minimo'])
        self.assertEqual(len(servicios.existencias_con_total(solo_bajo_minimo=True)), 1)

    def test_filtro_por_bodega_cuenta_solo_esa_bodega(self):
        self._entrada(10)
        self._entrada(7, self.otra)
        fila = servicios.existencias_con_total(bodega_id=self.otra.pk)[0]
        self.assertEqual(fila['total'], 7)

    def test_busqueda_por_texto(self):
        self.assertEqual(len(servicios.existencias_con_total('saber')), 1)
        self.assertEqual(len(servicios.existencias_con_total('zzz')), 0)
