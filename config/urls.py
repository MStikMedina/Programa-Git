"""Rutas del proyecto: Terceros en la raíz e Inventario móvil bajo /movil/."""
from django.urls import include, path

urlpatterns = [
    path('movil/', include('inventario_movil.urls')),
    path('', include('terceros.urls')),
]
