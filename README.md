# AAMO · Módulo Terceros (extracto)

Extracto ejecutable del módulo **Terceros** del inventario de logística de la plataforma
interna de Grupo Milton Ochoa (AAMO). Evidencias SENA: GA7-220501096-AA2-EV01 y EV02.

## Plataforma y equivalencias con lo pedido en la guía

AAMO está construido con **Python y Django** (plataforma elegida en AA1-EV01 y EV02), por lo que
las técnicas de la guía se aplican con su equivalente en esta plataforma:

| Pide la guía (Java)              | Se usa aquí (Python / Django)                                        |
|----------------------------------|----------------------------------------------------------------------|
| Conexión a BD con JDBC           | `django.db.connection` + cursor DB-API, SQL escrito a mano (`dao.py`) |
| `PreparedStatement` (`?`)        | Consultas parametrizadas con `%s`                                     |
| Servlet con `doGet` / `doPost`   | Vistas con `request.method` = `GET` / `POST` (`views.py`)            |
| Páginas JSP (`<c:forEach>`, EL)  | Plantillas Django (`{% for %}`, `{{ variable }}`)                    |
| `web.xml` / `@WebServlet`        | `urls.py`                                                             |

## Funcionalidades (CRUD)

* **Insertar**: `dao.insertar_tercero` · formulario `/nuevo/` (POST)
* **Consultar**: `dao.consultar_tercero`, `dao.listar_terceros` · lista `/` con filtros (GET)
* **Actualizar**: `dao.actualizar_tercero` · formulario `/<id>/editar/` (GET + POST)
* **Eliminar**: `dao.eliminar_tercero` · confirmación `/<id>/eliminar/` (GET + POST)

## Estándares de codificación aplicados (definidos en AA1-EV02)

* **Variables y funciones**: `snake_case` descriptivo (`tercero_id`, `listar_terceros`).
* **Clases**: `PascalCase` (`TerceroInvalido`, `TercerosConfig`).
* **Constantes**: `MAYUSCULAS_CON_GUION_BAJO` (`NOMBRE_TABLA`).
* **Paquetes y módulos**: minúsculas (`terceros`, `dao.py`).
* PEP 8 (4 espacios, imports agrupados), PEP 257 (docstrings), comillas simples para valores
  técnicos y dobles para textos que ve el usuario.

## Ejecución

```bash
pip install -r requirements.txt
python manage.py migrate        # crea la tabla log_terceros
python manage.py test           # 24 pruebas
python demo_consola.py          # demostración CRUD por consola
python manage.py runserver      # http://127.0.0.1:8000/
```

Base de datos: SQLite por defecto; para PostgreSQL (como en AAMO) basta cambiar `DATABASES`
en `config/settings.py`. La tabla es la misma `log_terceros` del proyecto real.


---

# Inventario móvil (GA7-220501096-AA3)

Módulo **móvil** (web móvil *mobile-first* instalable como PWA) del inventario de logística de AAMO,
hecho con Python y Django. Se abre en `/movil/`.

## Historias de usuario

| HU | Pantalla | Qué hace |
|----|----------|----------|
| HU-01 | Existencias | Lista de tarjetas con búsqueda, filtro por bodega y alerta de bajo mínimo |
| HU-02 | Entrada | Registra una entrada y suma el stock |
| HU-03 | Salida | Registra una salida; no permite sacar más de lo que hay |
| HU-04 | Kardex | Historial de movimientos del artículo con saldo |
| HU-05 | Artículo | Crea un artículo (categoría, referencia, grado 0°–11°, mínimo) |

## Estructura

* `models.py`: `Bodega`, `Articulo`, `Stock`, `Movimiento` (kardex).
* `servicios.py`: única puerta de escritura del stock (transacción atómica).
* `forms.py`: validaciones (fechas, números, textos, caracteres especiales, longitudes).
* `views.py` / `urls.py` / `templates/`: pantallas móviles, manifiesto PWA y service worker.

## Ejecución

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_demo     # datos de ejemplo
python manage.py runserver       # abrir http://localhost:8000/movil/
python manage.py test            # 67 pruebas
```
