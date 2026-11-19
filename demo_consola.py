"""Demostración por consola del CRUD con SQL directo (equivalente a un main() JDBC).

Uso:  python manage.py migrate   y luego   python demo_consola.py
"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from terceros import dao  # noqa: E402  (requiere django.setup() previo)


def mostrar(titulo):
    print(f"\n=== {titulo} ===")
    for tercero in dao.listar_terceros():
        estado = 'activo' if tercero['activo'] else 'inactivo'
        print(f"  [{tercero['id']}] {tercero['nombre']} · doc {tercero['documento'] or '—'} · {estado}")


def main():
    dao.crear_tabla()
    mostrar("Estado inicial")

    tercero_id = dao.insertar_tercero('Colegio Demo', 'DEMO-001', '3001234567', 'Creado desde la consola')
    mostrar("Después de INSERTAR")

    print("\nConsulta por id:", dao.consultar_tercero(tercero_id))

    dao.actualizar_tercero(tercero_id, 'Colegio Demo (actualizado)', 'DEMO-001', '3009999999', '', False)
    mostrar("Después de ACTUALIZAR")

    dao.eliminar_tercero(tercero_id)
    mostrar("Después de ELIMINAR")


if __name__ == '__main__':
    main()
