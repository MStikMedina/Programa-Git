"""Rutas del proyecto: el módulo Terceros cuelga de la raíz."""
from django.urls import include, path

urlpatterns = [
    path('', include('terceros.urls')),
]
