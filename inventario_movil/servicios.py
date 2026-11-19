"""Servicios de dominio: única puerta de escritura del stock.

Todo cambio de existencias ocurre dentro de una transacción atómica y deja
su fila en el kardex. Si algo falla, no queda nada escrito.
"""
from django.db import transaction
from django.db.models import Q, Sum

from inventario_movil.models import Articulo, Movimiento, Stock


class StockInsuficiente(Exception):
    """Se intentó sacar más unidades de las que hay en la bodega."""

    def __init__(self, disponible, solicitado):
        self.disponible = disponible
        self.solicitado = solicitado
        super().__init__(
            f"Stock insuficiente: hay {disponible} y se piden {solicitado}.")


def _aplicar_movimiento(articulo, bodega, tipo, cantidad, fecha, observaciones):
    """Actualiza el stock y registra el kardex dentro de una transacción."""
    with transaction.atomic():
        # select_for_update evita que dos celulares modifiquen la misma fila a
        # la vez (en SQLite no hace nada; en PostgreSQL sí bloquea la fila).
        stock, _ = Stock.objects.select_for_update().get_or_create(
            articulo=articulo, bodega=bodega)
        if tipo == Movimiento.Tipo.ENTRADA:
            nuevo_saldo = stock.cantidad + cantidad
        else:
            if cantidad > stock.cantidad:
                raise StockInsuficiente(stock.cantidad, cantidad)
            nuevo_saldo = stock.cantidad - cantidad
        stock.cantidad = nuevo_saldo
        stock.save(update_fields=['cantidad'])
        return Movimiento.objects.create(
            articulo=articulo, bodega=bodega, tipo=tipo, cantidad=cantidad,
            saldo_resultante=nuevo_saldo, fecha=fecha,
            observaciones=observaciones)


def registrar_entrada(*, articulo, bodega, cantidad, fecha, observaciones=''):
    """Suma ``cantidad`` unidades al stock de la bodega."""
    return _aplicar_movimiento(articulo, bodega, Movimiento.Tipo.ENTRADA,
                               cantidad, fecha, observaciones)


def registrar_salida(*, articulo, bodega, cantidad, fecha, observaciones=''):
    """Resta ``cantidad`` unidades; lanza ``StockInsuficiente`` si no alcanzan."""
    return _aplicar_movimiento(articulo, bodega, Movimiento.Tipo.SALIDA,
                               cantidad, fecha, observaciones)


def existencias_con_total(texto='', bodega_id=None, solo_bajo_minimo=False):
    """Devuelve los artículos activos con su total y su estado de alerta.

    Cada elemento es un diccionario con ``articulo``, ``total`` y ``bajo_minimo``.
    Si se indica ``bodega_id`` el total cuenta solo esa bodega.
    """
    articulos = Articulo.objects.filter(activo=True)
    if texto:
        # Busca el texto en categoría o referencia (sin distinguir mayúsculas).
        articulos = articulos.filter(
            Q(categoria__icontains=texto) | Q(referencia__icontains=texto))
    # Suma de existencias; con bodega se limita a las filas de esa bodega.
    condicion = Q(existencias__bodega_id=bodega_id) if bodega_id else None
    articulos = articulos.annotate(
        total=Sum('existencias__cantidad', filter=condicion))
    resultado = []
    for articulo in articulos:
        total = articulo.total or 0
        bajo_minimo = articulo.stock_minimo > 0 and total < articulo.stock_minimo
        if solo_bajo_minimo and not bajo_minimo:
            continue
        resultado.append({'articulo': articulo, 'total': total,
                          'bajo_minimo': bajo_minimo})
    return resultado
