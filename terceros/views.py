"""Vistas web del módulo Terceros.

Cada vista cumple el papel de un servlet: ``request.method`` distingue entre
``GET`` (mostrar la página o el formulario, como ``doGet``) y ``POST``
(procesar el formulario, como ``doPost``). Las plantillas HTML de
``templates/terceros`` cumplen el papel de las páginas JSP.
"""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from terceros import dao


def _leer_formulario(post):
    """Extrae del POST los campos del formulario como diccionario."""
    return {
        'nombre': post.get('nombre', ''),
        'documento': post.get('documento', ''),
        'telefono': post.get('telefono', ''),
        'notas': post.get('notas', ''),
        'activo': post.get('activo') == 'on',
    }


def _obtener_o_404(tercero_id):
    """Devuelve el tercero o lanza 404 si no existe."""
    tercero = dao.consultar_tercero(tercero_id)
    if tercero is None:
        raise Http404("El tercero no existe.")
    return tercero


@require_http_methods(['GET'])
def lista_terceros(request):
    """GET: consulta y lista los terceros; admite filtro ``?q=`` y ``?activos=1``."""
    texto = request.GET.get('q', '')
    solo_activos = request.GET.get('activos') == '1'
    contexto = {
        'terceros': dao.listar_terceros(texto, solo_activos),
        'q': texto,
        'solo_activos': solo_activos,
    }
    return render(request, 'terceros/lista.html', contexto)


@require_http_methods(['GET', 'POST'])
def crear_tercero(request):
    """GET: muestra el formulario vacío. POST: inserta el tercero."""
    if request.method == 'POST':
        datos = _leer_formulario(request.POST)
        try:
            dao.insertar_tercero(**datos)
        except dao.TerceroInvalido as error:
            messages.error(request, str(error))
            return render(request, 'terceros/formulario.html',
                          {'datos': datos, 'titulo': "Nuevo tercero"})
        messages.success(request, "Tercero creado correctamente.")
        return redirect('terceros:lista')

    datos = {'nombre': '', 'documento': '', 'telefono': '', 'notas': '', 'activo': True}
    return render(request, 'terceros/formulario.html',
                  {'datos': datos, 'titulo': "Nuevo tercero"})


@require_http_methods(['GET', 'POST'])
def editar_tercero(request, tercero_id):
    """GET: muestra el formulario con los datos actuales. POST: actualiza."""
    tercero = _obtener_o_404(tercero_id)

    if request.method == 'POST':
        datos = _leer_formulario(request.POST)
        try:
            dao.actualizar_tercero(tercero_id, **datos)
        except dao.TerceroInvalido as error:
            messages.error(request, str(error))
            return render(request, 'terceros/formulario.html',
                          {'datos': datos, 'titulo': "Editar tercero"})
        messages.success(request, "Tercero actualizado correctamente.")
        return redirect('terceros:lista')

    return render(request, 'terceros/formulario.html',
                  {'datos': tercero, 'titulo': "Editar tercero"})


@require_http_methods(['GET', 'POST'])
def eliminar_tercero_vista(request, tercero_id):
    """GET: pide confirmación. POST: elimina el tercero."""
    tercero = _obtener_o_404(tercero_id)

    if request.method == 'POST':
        dao.eliminar_tercero(tercero_id)
        messages.success(request, "Tercero eliminado correctamente.")
        return redirect('terceros:lista')

    return render(request, 'terceros/confirmar_eliminar.html', {'tercero': tercero})
