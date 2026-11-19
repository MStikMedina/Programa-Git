"""Carga datos de ejemplo para probar el módulo en el celular o en el navegador."""
from datetime import date

from django.core.management.base import BaseCommand

from inventario_movil import servicios
from inventario_movil.models import Articulo, Bodega


class Command(BaseCommand):
    help = "Crea bodegas, artículos y movimientos de ejemplo (idempotente)."

    def handle(self, *args, **opciones):
        bucaramanga, _ = Bodega.objects.get_or_create(nombre='Bucaramanga')
        Bodega.objects.get_or_create(nombre='Barranquilla')
        materiales = [('Simulacro', 'Saber 11', 11, 50), ('Simulacro', 'Saber 11', 10, 50),
                      ('Martes de Prueba', 'MP 2026', 5, 30), ('Cartilla', 'Pensar', 3, 20)]
        for categoria, referencia, grado, minimo in materiales:
            articulo, creado = Articulo.objects.get_or_create(
                categoria=categoria, referencia=referencia, grado=grado,
                defaults={'stock_minimo': minimo})
            if creado:
                servicios.registrar_entrada(
                    articulo=articulo, bodega=bucaramanga, cantidad=minimo + 40,
                    fecha=date.today(), observaciones="Carga inicial de demostración")
        self.stdout.write(self.style.SUCCESS("Datos de demostración listos."))
