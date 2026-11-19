"""Modelos del módulo Inventario móvil (extracto de logística de AAMO).

Reproduce, de forma simplificada, el dominio del inventario de AAMO:
un artículo existe por grado (0° a 11°), el stock se guarda por artículo y
bodega, y cada cambio deja una fila inmutable en el kardex (``Movimiento``).
"""
from django.db import models

# Grados escolares en los que existe cada material (igual que en AAMO).
GRADOS = [(grado, f'{grado}°') for grado in range(12)]


class Bodega(models.Model):
    """Lugar físico donde se guarda el material (por ejemplo, Bucaramanga)."""

    nombre = models.CharField(max_length=60, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'movil_bodegas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Articulo(models.Model):
    """Material que se mueve: categoría + referencia + grado."""

    categoria = models.CharField(max_length=60)
    referencia = models.CharField(max_length=60)
    grado = models.PositiveSmallIntegerField(choices=GRADOS)
    stock_minimo = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'movil_articulos'
        ordering = ['categoria', 'referencia', 'grado']
        constraints = [
            models.UniqueConstraint(
                fields=['categoria', 'referencia', 'grado'],
                name='articulo_unico_por_grado'),
            models.CheckConstraint(
                condition=models.Q(grado__lte=11),
                name='articulo_grado_hasta_11'),
        ]

    @property
    def nombre(self):
        """Texto que se muestra en las tarjetas del celular."""
        return f'{self.categoria} {self.referencia} · {self.grado}°'

    def __str__(self):
        return self.nombre


class Stock(models.Model):
    """Cantidad actual de un artículo en una bodega.

    Solo lo modifican las funciones de ``servicios.py``; las vistas nunca
    escriben aquí directamente.
    """

    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE,
                                 related_name='existencias')
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE,
                               related_name='existencias')
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'movil_stock'
        constraints = [
            models.UniqueConstraint(fields=['articulo', 'bodega'],
                                    name='stock_unico_por_bodega'),
        ]


class Movimiento(models.Model):
    """Fila del kardex: nunca se edita ni se borra (solo se agrega)."""

    class Tipo(models.TextChoices):
        ENTRADA = 'ENTRADA', "Entrada"
        SALIDA = 'SALIDA', "Salida"

    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT,
                                 related_name='movimientos')
    bodega = models.ForeignKey(Bodega, on_delete=models.PROTECT,
                               related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    cantidad = models.PositiveIntegerField()
    saldo_resultante = models.PositiveIntegerField()
    fecha = models.DateField()
    observaciones = models.CharField(max_length=200, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movil_movimientos'
        ordering = ['-creado_en', '-id']
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gt=0),
                                   name='movimiento_cantidad_positiva'),
        ]

    @property
    def delta(self):
        """Signo del movimiento: suma en las entradas, resta en las salidas."""
        return self.cantidad if self.tipo == self.Tipo.ENTRADA else -self.cantidad
