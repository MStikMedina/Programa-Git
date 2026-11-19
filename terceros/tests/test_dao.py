"""Pruebas de la capa de acceso a datos (CRUD con SQL directo)."""
from django.test import TestCase

from terceros import dao


class InsertarTerceroTest(TestCase):

    def test_inserta_y_devuelve_id(self):
        tercero_id = dao.insertar_tercero('Colegio San José', '900123', '3001112233')
        self.assertIsInstance(tercero_id, int)
        tercero = dao.consultar_tercero(tercero_id)
        self.assertEqual(tercero['nombre'], 'Colegio San José')
        self.assertTrue(tercero['activo'])

    def test_nombre_es_obligatorio(self):
        with self.assertRaises(dao.TerceroInvalido):
            dao.insertar_tercero('   ')

    def test_documento_duplicado_se_rechaza(self):
        dao.insertar_tercero('Uno', '123')
        with self.assertRaises(dao.TerceroDuplicado):
            dao.insertar_tercero('Dos', '123')

    def test_documento_vacio_puede_repetirse(self):
        dao.insertar_tercero('Uno')
        dao.insertar_tercero('Dos')
        self.assertEqual(len(dao.listar_terceros()), 2)

    def test_sql_injection_se_guarda_como_texto(self):
        malicioso = "x'); DROP TABLE log_terceros; --"
        dao.insertar_tercero(malicioso)
        self.assertEqual(dao.listar_terceros()[0]['nombre'], malicioso)


class ConsultarTerceroTest(TestCase):

    def test_consulta_inexistente_devuelve_none(self):
        self.assertIsNone(dao.consultar_tercero(9999))

    def test_listado_ordenado_y_filtrado(self):
        dao.insertar_tercero('Zeta', '1')
        dao.insertar_tercero('Alfa', '2')
        dao.insertar_tercero('Beta inactivo', '3', activo=False)
        self.assertEqual([t['nombre'] for t in dao.listar_terceros()],
                         ['Alfa', 'Beta inactivo', 'Zeta'])
        self.assertEqual(len(dao.listar_terceros(solo_activos=True)), 2)
        self.assertEqual(dao.listar_terceros('ALF')[0]['nombre'], 'Alfa')
        self.assertEqual(dao.listar_terceros('3')[0]['nombre'], 'Beta inactivo')


class ActualizarTerceroTest(TestCase):

    def test_actualiza_campos(self):
        tercero_id = dao.insertar_tercero('Viejo', '1')
        self.assertTrue(dao.actualizar_tercero(tercero_id, 'Nuevo', '1', '300', 'nota', False))
        tercero = dao.consultar_tercero(tercero_id)
        self.assertEqual((tercero['nombre'], tercero['telefono'], tercero['activo']),
                         ('Nuevo', '300', False))

    def test_actualizar_inexistente_devuelve_false(self):
        self.assertFalse(dao.actualizar_tercero(9999, 'Nadie'))

    def test_actualizar_con_documento_de_otro_falla(self):
        dao.insertar_tercero('Uno', '1')
        segundo = dao.insertar_tercero('Dos', '2')
        with self.assertRaises(dao.TerceroDuplicado):
            dao.actualizar_tercero(segundo, 'Dos', '1')


class EliminarTerceroTest(TestCase):

    def test_elimina(self):
        tercero_id = dao.insertar_tercero('Borrar')
        self.assertTrue(dao.eliminar_tercero(tercero_id))
        self.assertIsNone(dao.consultar_tercero(tercero_id))

    def test_eliminar_inexistente_devuelve_false(self):
        self.assertFalse(dao.eliminar_tercero(9999))
