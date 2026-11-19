"""Pruebas de las vistas web: métodos GET y POST, formularios y plantillas."""
from django.test import TestCase
from django.urls import reverse

from terceros import dao


class ListaTercerosTest(TestCase):

    def test_get_muestra_lista_y_filtra(self):
        dao.insertar_tercero('Colegio Norte', '10')
        dao.insertar_tercero('Colegio Sur', '20')
        respuesta = self.client.get(reverse('terceros:lista'), {'q': 'norte'})
        self.assertContains(respuesta, 'Colegio Norte')
        self.assertNotContains(respuesta, 'Colegio Sur')

    def test_lista_vacia_muestra_aviso(self):
        self.assertContains(self.client.get(reverse('terceros:lista')),
                            'No hay terceros que coincidan.')

    def test_lista_no_acepta_post(self):
        self.assertEqual(self.client.post(reverse('terceros:lista')).status_code, 405)


class CrearTerceroTest(TestCase):

    def test_get_muestra_formulario(self):
        respuesta = self.client.get(reverse('terceros:crear'))
        self.assertContains(respuesta, 'name="nombre"')
        self.assertContains(respuesta, 'csrfmiddlewaretoken')

    def test_post_crea_y_redirige(self):
        respuesta = self.client.post(reverse('terceros:crear'),
                                     {'nombre': 'Nuevo', 'documento': '55', 'activo': 'on'})
        self.assertRedirects(respuesta, reverse('terceros:lista'))
        self.assertEqual(dao.listar_terceros()[0]['documento'], '55')

    def test_post_invalido_vuelve_al_formulario_con_error(self):
        respuesta = self.client.post(reverse('terceros:crear'), {'nombre': ''})
        self.assertContains(respuesta, 'El nombre es obligatorio.')
        self.assertEqual(dao.listar_terceros(), [])

    def test_post_duplicado_muestra_error(self):
        dao.insertar_tercero('Uno', '7')
        respuesta = self.client.post(reverse('terceros:crear'),
                                     {'nombre': 'Otro', 'documento': '7'})
        self.assertContains(respuesta, 'Ya existe un tercero con el documento 7.')


class EditarTerceroTest(TestCase):

    def test_get_precarga_datos(self):
        tercero_id = dao.insertar_tercero('Editable', '9')
        respuesta = self.client.get(reverse('terceros:editar', args=[tercero_id]))
        self.assertContains(respuesta, 'value="Editable"')

    def test_post_actualiza(self):
        tercero_id = dao.insertar_tercero('Antes', '9')
        self.client.post(reverse('terceros:editar', args=[tercero_id]),
                         {'nombre': 'Después', 'documento': '9', 'activo': 'on'})
        self.assertEqual(dao.consultar_tercero(tercero_id)['nombre'], 'Después')

    def test_inexistente_da_404(self):
        self.assertEqual(self.client.get(reverse('terceros:editar', args=[999])).status_code, 404)


class EliminarTerceroTest(TestCase):

    def test_get_pide_confirmacion_y_no_borra(self):
        tercero_id = dao.insertar_tercero('Conservar')
        respuesta = self.client.get(reverse('terceros:eliminar', args=[tercero_id]))
        self.assertContains(respuesta, 'Conservar')
        self.assertIsNotNone(dao.consultar_tercero(tercero_id))

    def test_post_elimina(self):
        tercero_id = dao.insertar_tercero('Borrar')
        respuesta = self.client.post(reverse('terceros:eliminar', args=[tercero_id]))
        self.assertRedirects(respuesta, reverse('terceros:lista'))
        self.assertIsNone(dao.consultar_tercero(tercero_id))
