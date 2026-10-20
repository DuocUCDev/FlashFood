"""Pedido, sus líneas y el ciclo de estados.

Flujo:
CREADO → PAGADO → EN_PREPARACION → EN_CAMINO → ENTREGADO
   └──────────────→ CANCELADO

La cancelación es posible en Creado, Pagado y En preparación.
"""

from enum import Enum

from flashfood.modelo.errores import ReglaNegocioError
from flashfood.modelo.pago import MetodoPago, ResultadoPago
from flashfood.modelo.producto import Producto
from flashfood.modelo.validacion import exigir_entero, texto_obligatorio


class EstadoPedido(Enum):
    CREADO = "CREADO"
    PAGADO = "PAGADO"
    EN_PREPARACION = "EN_PREPARACION"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"

    @property
    def etiqueta(self) -> str:
        return {
            EstadoPedido.CREADO: "Creado",
            EstadoPedido.PAGADO: "Pagado",
            EstadoPedido.EN_PREPARACION: "En preparación",
            EstadoPedido.EN_CAMINO: "En camino",
            EstadoPedido.ENTREGADO: "Entregado",
            EstadoPedido.CANCELADO: "Cancelado",
        }[self]


_TRANSICIONES = {
    EstadoPedido.CREADO: {EstadoPedido.PAGADO, EstadoPedido.CANCELADO},
    EstadoPedido.PAGADO: {EstadoPedido.EN_PREPARACION, EstadoPedido.CANCELADO},
    EstadoPedido.EN_PREPARACION: {EstadoPedido.EN_CAMINO, EstadoPedido.CANCELADO},
    EstadoPedido.EN_CAMINO: {EstadoPedido.ENTREGADO},
    EstadoPedido.ENTREGADO: set(),
    EstadoPedido.CANCELADO: set(),
}


class DetallePedido:
    """Una línea: producto, cantidad, precio congelado y subtotal."""

    def __init__(self, producto_id: str, nombre: str, precio_unitario: int, cantidad: int):
        self._producto_id = texto_obligatorio(producto_id, "Producto")
        self._nombre = texto_obligatorio(nombre, "Nombre del producto")
        self._precio_unitario = exigir_entero(precio_unitario, "Precio", minimo=1)
        self._cantidad = exigir_entero(cantidad, "Cantidad", minimo=1)

    @property
    def producto_id(self) -> str:
        return self._producto_id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def precio_unitario(self) -> int:
        return self._precio_unitario

    @property
    def cantidad(self) -> int:
        return self._cantidad

    @property
    def subtotal(self) -> int:
        return self._precio_unitario * self._cantidad

    def aumentar(self, cantidad: int) -> None:
        cantidad = exigir_entero(cantidad, "Cantidad", minimo=1)
        self._cantidad += cantidad

    def a_diccionario(self) -> dict:
        return {
            "producto_id": self._producto_id,
            "nombre": self._nombre,
            "precio_unitario": self._precio_unitario,
            "cantidad": self._cantidad,
        }

    @classmethod
    def desde_diccionario(cls, datos: dict) -> "DetallePedido":
        try:
            return cls(
                datos["producto_id"],
                datos["nombre"],
                datos["precio_unitario"],
                datos["cantidad"],
            )
        except (KeyError, TypeError) as error:
            raise ReglaNegocioError("Línea de pedido incompleta") from error


class Pedido:
    """Compra de un cliente. Calcula subtotal, despacho, descuento y total.

    Despacho base: $2.000.
    Hora punta: ese despacho aumenta un 25%.
    Lluvia: se suman $1.000 al despacho, después del ajuste de hora punta.
    Cliente VIP: 10% de descuento sobre el subtotal. El despacho no se descuenta.
    """

    DESPACHO_BASE = 2000
    RECARGO_LLUVIA = 1000
    PORCENTAJE_HORA_PUNTA = 25
    PORCENTAJE_VIP = 10

    def __init__(self, id: str, cliente_id: str, es_vip: bool, hora_punta: bool, lluvia: bool):
        if type(es_vip) is not bool or type(hora_punta) is not bool or type(lluvia) is not bool:
            raise ReglaNegocioError("Las condiciones del pedido deben ser sí o no")
        self._id = texto_obligatorio(id, "Identificador")
        self._cliente_id = texto_obligatorio(cliente_id, "Cliente")
        self._es_vip = es_vip
        self._hora_punta = hora_punta
        self._lluvia = lluvia
        self._detalles: list[DetallePedido] = []
        self._estado = EstadoPedido.CREADO
        self._historial: list[EstadoPedido] = [EstadoPedido.CREADO]
        self._repartidor_id: str | None = None
        self._pago: ResultadoPago | None = None
        self._stock_descontado = False
        self._stock_restituido = False

    @property
    def id(self) -> str:
        return self._id

    @property
    def cliente_id(self) -> str:
        return self._cliente_id

    @property
    def es_vip(self) -> bool:
        return self._es_vip

    @property
    def hora_punta(self) -> bool:
        return self._hora_punta

    @property
    def lluvia(self) -> bool:
        return self._lluvia

    @property
    def estado(self) -> EstadoPedido:
        return self._estado

    @property
    def historial(self) -> tuple[EstadoPedido, ...]:
        return tuple(self._historial)

    @property
    def detalles(self) -> tuple[DetallePedido, ...]:
        return tuple(self._detalles)

    @property
    def repartidor_id(self) -> str | None:
        return self._repartidor_id

    @property
    def pago(self) -> ResultadoPago | None:
        return self._pago

    @property
    def stock_descontado(self) -> bool:
        return self._stock_descontado

    @property
    def stock_restituido(self) -> bool:
        return self._stock_restituido

    @property
    def subtotal(self) -> int:
        return sum(detalle.subtotal for detalle in self._detalles)

    @property
    def descuento(self) -> int:
        if not self._es_vip:
            return 0
        return self.subtotal * self.PORCENTAJE_VIP // 100

    @property
    def costo_despacho(self) -> int:
        costo = self.DESPACHO_BASE
        if self._hora_punta:
            costo += self.DESPACHO_BASE * self.PORCENTAJE_HORA_PUNTA // 100
        if self._lluvia:
            costo += self.RECARGO_LLUVIA
        return costo

    @property
    def total(self) -> int:
        return self.subtotal - self.descuento + self.costo_despacho

    def historial_texto(self) -> str:
        return " → ".join(estado.etiqueta for estado in self._historial)

    def cantidad_de(self, producto_id: str) -> int:
        for detalle in self._detalles:
            if detalle.producto_id == producto_id:
                return detalle.cantidad
        return 0

    def contiene(self, producto_id: str) -> bool:
        return any(detalle.producto_id == producto_id for detalle in self._detalles)

    def agregar(self, producto: Producto, cantidad: int) -> None:
        self._exigir_editable()
        cantidad = exigir_entero(cantidad, "Cantidad", minimo=1)
        for detalle in self._detalles:
            if detalle.producto_id == producto.id:
                detalle.aumentar(cantidad)
                return
        self._detalles.append(
            DetallePedido(producto.id, producto.nombre, producto.precio, cantidad)
        )

    def quitar(self, producto_id: str) -> None:
        self._exigir_editable()
        restantes = [detalle for detalle in self._detalles if detalle.producto_id != producto_id]
        if len(restantes) == len(self._detalles):
            raise ReglaNegocioError("Ese producto no está en el pedido")
        self._detalles = restantes

    def validar_puede_pagarse(self) -> None:
        if self._pago is not None or self._estado is not EstadoPedido.CREADO:
            raise ReglaNegocioError("El pedido no se puede pagar en su estado actual")
        if not self._detalles:
            raise ReglaNegocioError("Agrega productos antes de pagar")

    def cobrar(self, metodo: MetodoPago) -> ResultadoPago:
        """Polimorfismo: procesar depende de la clase concreta del medio."""
        self.validar_puede_pagarse()
        if not isinstance(metodo, MetodoPago):
            raise ReglaNegocioError("Medio de pago no válido")
        return metodo.procesar(self.total)

    def confirmar_pago(self, resultado: ResultadoPago) -> None:
        self.validar_puede_pagarse()
        if not resultado.aprobado:
            raise ReglaNegocioError("Un pago rechazado no confirma el pedido")
        self._pago = resultado
        self._stock_descontado = True
        self._transicionar(EstadoPedido.PAGADO)

    def preparar(self) -> None:
        self._transicionar(EstadoPedido.EN_PREPARACION)

    def asignar_repartidor(self, repartidor_id: str) -> None:
        if self._estado is not EstadoPedido.EN_PREPARACION:
            raise ReglaNegocioError("Solo se asigna un repartidor con el pedido en preparación")
        if self._repartidor_id:
            raise ReglaNegocioError("El pedido ya tiene un repartidor")
        self._repartidor_id = texto_obligatorio(repartidor_id, "Repartidor")

    def despachar(self) -> None:
        if not self._repartidor_id:
            raise ReglaNegocioError("Asigna un repartidor antes de despachar")
        self._transicionar(EstadoPedido.EN_CAMINO)

    def entregar(self) -> None:
        if self._estado is EstadoPedido.ENTREGADO:
            raise ReglaNegocioError("El pedido entregado mantiene su estado final")
        self._transicionar(EstadoPedido.ENTREGADO)

    def puede_cancelarse(self) -> bool:
        return EstadoPedido.CANCELADO in _TRANSICIONES[self._estado]

    def marcar_stock_restituido(self) -> None:
        if self._stock_restituido:
            raise ReglaNegocioError("El stock de este pedido ya fue restituido")
        if not self._stock_descontado:
            raise ReglaNegocioError("Este pedido no tiene stock descontado")
        self._stock_restituido = True

    def cancelar(self) -> None:
        if self._estado is EstadoPedido.ENTREGADO:
            raise ReglaNegocioError("El pedido entregado mantiene su estado final")
        self._transicionar(EstadoPedido.CANCELADO)

    def a_diccionario(self) -> dict:
        return {
            "id": self._id,
            "cliente_id": self._cliente_id,
            "es_vip": self._es_vip,
            "hora_punta": self._hora_punta,
            "lluvia": self._lluvia,
            "estado": self._estado.value,
            "historial": [estado.value for estado in self._historial],
            "repartidor_id": self._repartidor_id,
            "stock_descontado": self._stock_descontado,
            "stock_restituido": self._stock_restituido,
            "pago": None if self._pago is None else self._pago.a_diccionario(),
            "detalles": [detalle.a_diccionario() for detalle in self._detalles],
        }

    @classmethod
    def desde_diccionario(cls, datos: dict) -> "Pedido":
        try:
            pedido = cls(
                datos["id"],
                datos["cliente_id"],
                datos["es_vip"],
                datos["hora_punta"],
                datos["lluvia"],
            )
            pedido._detalles = [DetallePedido.desde_diccionario(item) for item in datos["detalles"]]
            pedido._estado = EstadoPedido(datos["estado"])
            pedido._historial = [EstadoPedido(valor) for valor in datos["historial"]]
            pedido._repartidor_id = datos["repartidor_id"]
            pedido._stock_descontado = datos["stock_descontado"]
            pedido._stock_restituido = datos["stock_restituido"]
            pago = datos["pago"]
            pedido._pago = None if pago is None else ResultadoPago.desde_diccionario(pago)
        except (KeyError, TypeError, ValueError) as error:
            raise ReglaNegocioError("Pedido guardado incompleto o inválido") from error
        pedido._validar_rehidratacion()
        return pedido

    def _exigir_editable(self) -> None:
        if self._estado is not EstadoPedido.CREADO:
            raise ReglaNegocioError("Solo se modifican los productos de un pedido creado")

    def _transicionar(self, nuevo: EstadoPedido) -> None:
        if nuevo not in _TRANSICIONES[self._estado]:
            raise ReglaNegocioError(
                f"No se puede pasar de {self._estado.etiqueta} a {nuevo.etiqueta}"
            )
        self._estado = nuevo
        self._historial.append(nuevo)

    def _validar_rehidratacion(self) -> None:
        if type(self._stock_descontado) is not bool or type(self._stock_restituido) is not bool:
            raise ReglaNegocioError("El registro de stock del pedido es inválido")
        if self._repartidor_id is not None and not isinstance(self._repartidor_id, str):
            raise ReglaNegocioError("El repartidor guardado es inválido")
        if not self._historial or self._historial[0] is not EstadoPedido.CREADO:
            raise ReglaNegocioError("El historial del pedido es inválido")
        if self._historial[-1] is not self._estado:
            raise ReglaNegocioError("El historial no coincide con el estado del pedido")
        pagado_o_posterior = self._estado in {
            EstadoPedido.PAGADO,
            EstadoPedido.EN_PREPARACION,
            EstadoPedido.EN_CAMINO,
            EstadoPedido.ENTREGADO,
        }
        if pagado_o_posterior and (self._pago is None or not self._pago.aprobado or not self._stock_descontado):
            raise ReglaNegocioError("Un pedido confirmado debe tener pago aprobado y stock descontado")
        if self._estado is EstadoPedido.CREADO and (self._pago is not None or self._stock_descontado):
            raise ReglaNegocioError("Un pedido creado no puede tener pago confirmado")
        if self._stock_restituido and self._estado is not EstadoPedido.CANCELADO:
            raise ReglaNegocioError("El stock restituido solo corresponde a un pedido cancelado")
        if self._estado in {EstadoPedido.EN_CAMINO, EstadoPedido.ENTREGADO} and not self._repartidor_id:
            raise ReglaNegocioError("Un pedido despachado debe recordar a su repartidor")

    @staticmethod
    def texto_reglas() -> str:
        return (
            f"Despacho base ${Pedido.DESPACHO_BASE}. "
            f"Hora punta: +{Pedido.PORCENTAJE_HORA_PUNTA}% sobre el despacho. "
            f"Lluvia: +${Pedido.RECARGO_LLUVIA} adicionales. "
            f"Cliente VIP: {Pedido.PORCENTAJE_VIP}% de descuento sobre el subtotal."
        )
