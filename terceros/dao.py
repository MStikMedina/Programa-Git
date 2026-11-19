"""Capa de acceso a datos del módulo Terceros (patrón DAO).

Equivale al uso de JDBC en Java: se trabaja con SQL escrito a mano sobre una
conexión de la base de datos, sin pasar por el ORM. Django entrega la conexión
(``connection``) y un cursor que sigue la especificación DB-API de Python, el
mismo papel que cumplen ``Connection`` y ``PreparedStatement`` en JDBC.

Reglas aplicadas:
    * Todas las consultas son parametrizadas (``%s``): nunca se concatenan
      valores dentro del SQL, lo que evita la inyección SQL.
    * Cada función hace una sola cosa (insertar, consultar, actualizar o
      eliminar) y devuelve tipos simples (``int``, ``bool``, ``dict``, ``list``).
    * Los errores de negocio se expresan con excepciones propias.

La tabla coincide con ``log_terceros`` del inventario de logística de AAMO.
"""
from django.db import IntegrityError, connection

NOMBRE_TABLA = 'log_terceros'
LONGITUD_MAXIMA_NOMBRE = 200
LONGITUD_MAXIMA_DOCUMENTO = 50
LONGITUD_MAXIMA_TELEFONO = 50

COLUMNAS = ('id', 'nombre', 'documento', 'telefono', 'notas', 'activo')


class TerceroInvalido(ValueError):
    """Los datos recibidos no cumplen las reglas de negocio."""


class TerceroDuplicado(TerceroInvalido):
    """Ya existe otro tercero con el mismo documento."""


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _fila_a_diccionario(fila):
    """Convierte una fila (tupla) en un diccionario con los nombres de columna."""
    tercero = dict(zip(COLUMNAS, fila))
    tercero['activo'] = bool(tercero['activo'])
    return tercero


def _validar_datos(nombre, documento, telefono):
    """Valida y normaliza los campos de texto; devuelve (nombre, documento, telefono)."""
    nombre = (nombre or '').strip()
    documento = (documento or '').strip()
    telefono = (telefono or '').strip()

    if not nombre:
        raise TerceroInvalido("El nombre es obligatorio.")
    if len(nombre) > LONGITUD_MAXIMA_NOMBRE:
        raise TerceroInvalido(
            f"El nombre no puede superar {LONGITUD_MAXIMA_NOMBRE} caracteres.")
    if len(documento) > LONGITUD_MAXIMA_DOCUMENTO:
        raise TerceroInvalido(
            f"El documento no puede superar {LONGITUD_MAXIMA_DOCUMENTO} caracteres.")
    if len(telefono) > LONGITUD_MAXIMA_TELEFONO:
        raise TerceroInvalido(
            f"El teléfono no puede superar {LONGITUD_MAXIMA_TELEFONO} caracteres.")
    return nombre, documento, telefono


# ---------------------------------------------------------------------------
# Esquema
# ---------------------------------------------------------------------------

def crear_tabla():
    """Crea la tabla y su índice único si todavía no existen.

    El tipo de la llave primaria cambia según el motor (SQLite o PostgreSQL);
    el resto del SQL es idéntico en ambos.
    """
    llave = ('INTEGER PRIMARY KEY AUTOINCREMENT'
             if connection.vendor == 'sqlite' else 'BIGSERIAL PRIMARY KEY')
    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {NOMBRE_TABLA} (
                id {llave},
                nombre VARCHAR({LONGITUD_MAXIMA_NOMBRE}) NOT NULL,
                documento VARCHAR({LONGITUD_MAXIMA_DOCUMENTO}) NOT NULL DEFAULT '',
                telefono VARCHAR({LONGITUD_MAXIMA_TELEFONO}) NOT NULL DEFAULT '',
                notas TEXT NOT NULL DEFAULT '',
                activo BOOLEAN NOT NULL DEFAULT TRUE
            )
        """)
        # El documento solo es único cuando se diligencia (vacío se puede repetir).
        cursor.execute(f"""
            CREATE UNIQUE INDEX IF NOT EXISTS unique_tercero_documento
            ON {NOMBRE_TABLA} (documento) WHERE documento <> ''
        """)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def insertar_tercero(nombre, documento='', telefono='', notas='', activo=True):
    """INSERT: crea un tercero y devuelve su id."""
    nombre, documento, telefono = _validar_datos(nombre, documento, telefono)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO {NOMBRE_TABLA} (nombre, documento, telefono, notas, activo) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                [nombre, documento, telefono, notas or '', bool(activo)],
            )
            return cursor.fetchone()[0]
    except IntegrityError as error:
        raise TerceroDuplicado(
            f"Ya existe un tercero con el documento {documento}.") from error


def consultar_tercero(tercero_id):
    """SELECT por llave primaria: devuelve un diccionario o ``None`` si no existe."""
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT {', '.join(COLUMNAS)} FROM {NOMBRE_TABLA} WHERE id = %s",
            [tercero_id],
        )
        fila = cursor.fetchone()
    return _fila_a_diccionario(fila) if fila else None


def listar_terceros(texto='', solo_activos=False):
    """SELECT con filtros: lista ordenada por nombre.

    ``texto`` busca (sin distinguir mayúsculas) dentro del nombre o del documento.
    """
    condiciones = []
    parametros = []
    texto = (texto or '').strip()
    if texto:
        condiciones.append("(LOWER(nombre) LIKE %s OR LOWER(documento) LIKE %s)")
        patron = f"%{texto.lower()}%"
        parametros.extend([patron, patron])
    if solo_activos:
        condiciones.append("activo = %s")
        parametros.append(True)

    sql = f"SELECT {', '.join(COLUMNAS)} FROM {NOMBRE_TABLA}"
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY nombre, id"

    with connection.cursor() as cursor:
        cursor.execute(sql, parametros)
        return [_fila_a_diccionario(fila) for fila in cursor.fetchall()]


def actualizar_tercero(tercero_id, nombre, documento='', telefono='', notas='', activo=True):
    """UPDATE: modifica un tercero; devuelve ``True`` si la fila existía."""
    nombre, documento, telefono = _validar_datos(nombre, documento, telefono)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {NOMBRE_TABLA} "
                "SET nombre = %s, documento = %s, telefono = %s, notas = %s, activo = %s "
                "WHERE id = %s",
                [nombre, documento, telefono, notas or '', bool(activo), tercero_id],
            )
            return cursor.rowcount > 0
    except IntegrityError as error:
        raise TerceroDuplicado(
            f"Ya existe otro tercero con el documento {documento}.") from error


def eliminar_tercero(tercero_id):
    """DELETE: borra un tercero; devuelve ``True`` si la fila existía."""
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {NOMBRE_TABLA} WHERE id = %s", [tercero_id])
        return cursor.rowcount > 0
