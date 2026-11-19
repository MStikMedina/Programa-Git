"""Vistas móviles del inventario: GET muestra la pantalla, POST procesa el formulario."""
from datetime import date

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from inventario_movil import servicios
from inventario_movil.forms import ArticuloForm, MovimientoForm
from inventario_movil.models import Articulo, Bodega, Movimiento


@require_GET
def existencias(request):
    """HU-01: lista de tarjetas con búsqueda, filtro de bodega y alerta de mínimo."""
    texto = request.GET.get('q', '').strip()
    bodega_id = request.GET.get('bodega') or None
    if bodega_id is not None and not bodega_id.isdigit():
        bodega_id = None  # un valor raro se ignora en vez de romper la página
    solo_bajo = request.GET.get('bajo') == '1'
    contexto = {
        'filas': servicios.existencias_con_total(texto, bodega_id, solo_bajo),
        'bodegas': Bodega.objects.filter(activa=True),
        'q': texto, 'bodega_id': bodega_id, 'solo_bajo': solo_bajo,
        'seccion': 'existencias',
    }
    return render(request, 'inventario_movil/existencias.html', contexto)


@require_GET
def kardex(request, articulo_id):
    """HU-04: historial de movimientos de un artículo con su saldo."""
    articulo = get_object_or_404(Articulo, pk=articulo_id)
    contexto = {
        'articulo': articulo,
        'movimientos': articulo.movimientos.select_related('bodega')[:100],
        'existencias': articulo.existencias.select_related('bodega'),
        'seccion': 'existencias',
    }
    return render(request, 'inventario_movil/kardex.html', contexto)


def _vista_movimiento(request, tipo):
    """Lógica compartida de entrada y salida (mismo formulario, distinta regla)."""
    es_entrada = tipo == Movimiento.Tipo.ENTRADA
    if request.method == 'POST':
        formulario = MovimientoForm(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            registrar = (servicios.registrar_entrada if es_entrada
                         else servicios.registrar_salida)
            try:
                movimiento = registrar(**datos)
            except servicios.StockInsuficiente as error:
                formulario.add_error('cantidad', str(error))
            else:
                messages.success(
                    request, f"{'Entrada' if es_entrada else 'Salida'} registrada. "
                             f"Saldo: {movimiento.saldo_resultante}.")
                return redirect('inventario_movil:kardex',
                                articulo_id=datos['articulo'].pk)
    else:
        formulario = MovimientoForm(initial={'fecha': date.today()})
    return render(request, 'inventario_movil/movimiento.html', {
        'formulario': formulario, 'es_entrada': es_entrada,
        'titulo': "Registrar entrada" if es_entrada else "Registrar salida",
        'seccion': 'entrada' if es_entrada else 'salida',
    })


@require_http_methods(['GET', 'POST'])
def entrada(request):
    """HU-02: registrar una entrada de material."""
    return _vista_movimiento(request, Movimiento.Tipo.ENTRADA)


@require_http_methods(['GET', 'POST'])
def salida(request):
    """HU-03: registrar una salida de material (valida que haya stock)."""
    return _vista_movimiento(request, Movimiento.Tipo.SALIDA)


@require_http_methods(['GET', 'POST'])
def nuevo_articulo(request):
    """HU-05: crear un artículo nuevo."""
    formulario = ArticuloForm(request.POST or None)
    if request.method == 'POST' and formulario.is_valid():
        articulo = formulario.save()
        messages.success(request, f"Artículo creado: {articulo.nombre}.")
        return redirect('inventario_movil:existencias')
    return render(request, 'inventario_movil/articulo_form.html',
                  {'formulario': formulario, 'seccion': 'articulo'})


# --- Soporte PWA: permite "instalar" la pantalla en el celular ---------------

@require_GET
def manifest(request):
    """Manifiesto de la aplicación web progresiva (nombre, colores, icono)."""
    return JsonResponse({
        'name': "AAMO Inventario móvil", 'short_name': "Inventario",
        'start_url': '/movil/', 'scope': '/movil/', 'display': 'standalone',
        'background_color': '#ffffff', 'theme_color': '#0d6efd',
        'icons': [{'src': '/static/inventario_movil/icono.svg',
                   'sizes': 'any', 'type': 'image/svg+xml'}],
    }, content_type='application/manifest+json')


@require_GET
def service_worker(request):
    """Service worker mínimo: guarda en caché los estilos para abrir más rápido."""
    codigo = (
        "const CACHE = 'inventario-movil-v1';\n"
        "self.addEventListener('install', e => e.waitUntil(\n"
        "  caches.open(CACHE).then(c => c.add('/static/inventario_movil/app.css'))));\n"
        "self.addEventListener('fetch', e => {\n"
        "  if (e.request.url.includes('/static/')) {\n"
        "    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));\n"
        "  }\n"
        "});\n"
    )
    return HttpResponse(codigo, content_type='application/javascript')
