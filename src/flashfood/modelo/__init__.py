"""Modelo de dominio. No importa Tkinter."""

from flashfood.modelo.cliente import Cliente
from flashfood.modelo.errores import PersistenciaError, ReglaNegocioError
from flashfood.modelo.pago import (
    MetodoPago,
    PagoBilletera,
    PagoEfectivo,
    PagoTarjeta,
    PagoTransferencia,
    ResultadoPago,
)
from flashfood.modelo.pedido import DetallePedido, EstadoPedido, Pedido
from flashfood.modelo.producto import Bebida, Comida, Producto
from flashfood.modelo.repartidor import Repartidor
from flashfood.modelo.sistema import FlashFood

__all__ = [
    "Bebida",
    "Cliente",
    "Comida",
    "DetallePedido",
    "EstadoPedido",
    "FlashFood",
    "MetodoPago",
    "PagoBilletera",
    "PagoEfectivo",
    "PagoTarjeta",
    "PagoTransferencia",
    "Pedido",
    "PersistenciaError",
    "Producto",
    "ReglaNegocioError",
    "Repartidor",
    "ResultadoPago",
]
