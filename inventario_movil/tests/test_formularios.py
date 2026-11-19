"""Pruebas de validación: fechas, números, textos, caracteres especiales y longitudes."""
from datetime import date, timedelta

from django.test import TestCase

from inventario_movil.forms import ArticuloForm, MovimientoForm
from inventario_movil.models import Articulo, Bodega


class ArticuloFormTest(TestCase):
    def _form(self, **cambios):
        datos = {'categoria': 'Simulacro', 'referencia': 'Saber 11', 'grado': 11,
                 'stock_minimo': 20}
        datos.update(cambios)
        return ArticuloForm(datos)

    def test_datos_validos(self):
        self.assertTrue(self._form().is_valid())

    def test_texto_con_caracteres_especiales_se_rechaza(self):
        for texto in ['<script>', 'Saber;11', 'a"b', "x'y", 'Ref#1']:
            self.assertFalse(self._form(referencia=texto).is_valid(), texto)

    def test_texto_con_tildes_y_enie_se_acepta(self):
        self.assertTrue(self._form(categoria='Año Escolar Ñandú').is_valid())

    def test_texto_vacio_o_solo_espacios_se_rechaza(self):
        self.assertFalse(self._form(categoria='   ').is_valid())

    def test_longitud_maxima_60(self):
        self.assertFalse(self._form(categoria='a' * 61).is_valid())
        self.assertTrue(self._form(categoria='a' * 60).is_valid())

    def test_grado_fuera_de_rango_se_rechaza(self):
        self.assertFalse(self._form(grado=12).is_valid())
        self.assertFalse(self._form(grado=-1).is_valid())

    def test_stock_minimo_negativo_o_texto_se_rechaza(self):
        self.assertFalse(self._form(stock_minimo=-5).is_valid())
        self.assertFalse(self._form(stock_minimo='abc').is_valid())

    def test_espacios_repetidos_se_colapsan(self):
        formulario = self._form(referencia='Saber    11')
        self.assertTrue(formulario.is_valid())
        self.assertEqual(formulario.cleaned_data['referencia'], 'Saber 11')


class MovimientoFormTest(TestCase):
    def setUp(self):
        self.bodega = Bodega.objects.create(nombre='Bucaramanga')
        self.articulo = Articulo.objects.create(categoria='S', referencia='R', grado=1)

    def _form(self, **cambios):
        datos = {'articulo': self.articulo.pk, 'bodega': self.bodega.pk, 'cantidad': 5,
                 'fecha': date.today().isoformat(), 'observaciones': ''}
        datos.update(cambios)
        return MovimientoForm(datos)

    def test_datos_validos(self):
        self.assertTrue(self._form().is_valid())

    def test_cantidad_cero_negativa_decimal_o_texto_se_rechaza(self):
        for valor in [0, -3, '2.5', 'diez', '']:
            self.assertFalse(self._form(cantidad=valor).is_valid(), valor)

    def test_cantidad_sobre_el_maximo_se_rechaza(self):
        self.assertFalse(self._form(cantidad=100001).is_valid())
        self.assertTrue(self._form(cantidad=100000).is_valid())

    def test_fecha_futura_se_rechaza(self):
        manana = (date.today() + timedelta(days=1)).isoformat()
        formulario = self._form(fecha=manana)
        self.assertFalse(formulario.is_valid())
        self.assertIn("futura", formulario.errors['fecha'][0])

    def test_fecha_invalida_se_rechaza(self):
        for valor in ['2026-02-30', 'hoy', '31/12/2026x', '']:
            self.assertFalse(self._form(fecha=valor).is_valid(), valor)

    def test_observaciones_largas_se_rechazan(self):
        self.assertFalse(self._form(observaciones='x' * 201).is_valid())
        self.assertTrue(self._form(observaciones='x' * 200).is_valid())

    def test_observaciones_con_caracter_de_control_se_rechazan(self):
        self.assertFalse(self._form(observaciones='hola\x00mundo').is_valid())

    def test_bodega_inactiva_o_inexistente_se_rechaza(self):
        self.bodega.activa = False
        self.bodega.save()
        self.assertFalse(self._form().is_valid())
        self.assertFalse(self._form(bodega=999).is_valid())
