"""Rutas del módulo Inventario móvil."""
from django.urls import path

from inventario_movil import views

app_name = 'inventario_movil'

urlpatterns = [
    path('', views.existencias, name='existencias'),
    path('articulo/nuevo/', views.nuevo_articulo, name='articulo_nuevo'),
    path('articulo/<int:articulo_id>/', views.kardex, name='kardex'),
    path('entrada/', views.entrada, name='entrada'),
    path('salida/', views.salida, name='salida'),
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='sw'),
]
