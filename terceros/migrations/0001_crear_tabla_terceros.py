"""Crea la tabla log_terceros con SQL directo (ver terceros/dao.py)."""
from django.db import migrations

from terceros import dao


def crear(apps, schema_editor):
    dao.crear_tabla()


def borrar(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {dao.NOMBRE_TABLA}")


class Migration(migrations.Migration):

    initial = True
    dependencies = []
    operations = [migrations.RunPython(crear, borrar)]
