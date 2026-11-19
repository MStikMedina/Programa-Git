"""Rutas del módulo Terceros."""
from django.urls import path

from terceros import views

app_name = 'terceros'

urlpatterns = [
    path('', views.lista_terceros, name='lista'),
    path('nuevo/', views.crear_tercero, name='crear'),
    path('<int:tercero_id>/editar/', views.editar_tercero, name='editar'),
    path('<int:tercero_id>/eliminar/', views.eliminar_tercero_vista, name='eliminar'),
]
