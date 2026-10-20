"""Medios de pago. Cada subclase implementa la misma operación de cobro."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from flashfood.modelo.errores import ReglaNegocioError
from flashfood.modelo.formato import pesos
from flashfood.modelo.validacion import booleano, exigir_entero, texto_obligatorio


@dataclass(frozen=True)
class ResultadoPago:
    aprobado: bool
    referencia: str
    medio: str
    mensaje: str

    def a_diccionario(self) -> dict:
        return {
            "aprobado": self.aprobado,
            "referencia": self.referencia,
            "medio": self.medio,
            "mensaje": self.mensaje,
        }

    @classmethod
    def desde_diccionario(cls, datos: dict) -> "ResultadoPago":
        if not isinstance(datos, dict):
            raise ReglaNegocioError("El pago guardado no tiene el formato esperado")
        try:
            aprobado = datos["aprobado"]
            referencia = datos["referencia"]
            medio = datos["medio"]
            mensaje = datos["mensaje"]
        except KeyError as error:
            raise ReglaNegocioError("Pago guardado incompleto") from error
        if type(aprobado) is not bool or not isinstance(referencia, str) or not isinstance(medio, str):
            raise ReglaNegocioError("El resultado de pago guardado es inválido")
        if aprobado and not referencia.strip():
            raise ReglaNegocioError("Un pago aprobado debe tener referencia")
        return cls(aprobado, referencia, medio, str(mensaje))


class MetodoPago(ABC):
    """Contrato de cobro. El pedido no pregunta qué clase concreta lo atiende."""

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre visible del medio."""

    @abstractmethod
    def procesar(self, monto: int) -> ResultadoPago:
        """Simula el cobro. No mueve dinero real."""

    def anular(self, resultado: ResultadoPago) -> None:
        """Revierte un cobro aprobado si la compra no pudo confirmarse."""
        return None


def _validar_monto(monto: int) -> None:
    exigir_entero(monto, "Monto", minimo=1)


class PagoTarjeta(MetodoPago):
    def __init__(self, aprobado: bool = True):
        self._aprobado = booleano(aprobado, "La simulación de la tarjeta")

    @property
    def nombre(self) -> str:
        return "Tarjeta"

    def procesar(self, monto: int) -> ResultadoPago:
        _validar_monto(monto)
        if not self._aprobado:
            return ResultadoPago(False, "", self.nombre, "El pago con tarjeta fue rechazado")
        return ResultadoPago(True, f"TAR-{uuid4().hex[:8].upper()}", self.nombre, "Pago con tarjeta aprobado")


class PagoEfectivo(MetodoPago):
    def __init__(self, monto_entregado: int):
        self._monto_entregado = exigir_entero(monto_entregado, "Monto recibido", minimo=1)

    @property
    def nombre(self) -> str:
        return "Efectivo"

    def procesar(self, monto: int) -> ResultadoPago:
        _validar_monto(monto)
        if self._monto_entregado < monto:
            return ResultadoPago(False, "", self.nombre, "El efectivo no alcanza para cubrir el total")
        vuelto = self._monto_entregado - monto
        return ResultadoPago(
            True,
            f"EFE-{uuid4().hex[:8].upper()}",
            self.nombre,
            f"Pago en efectivo aprobado. Vuelto: {pesos(vuelto)}",
        )


class PagoBilletera(MetodoPago):
    def __init__(self, saldo: int):
        self._saldo = exigir_entero(saldo, "Saldo", minimo=0)
        self._ultimo_cargo = 0

    @property
    def nombre(self) -> str:
        return "Billetera digital"

    @property
    def saldo(self) -> int:
        return self._saldo

    def procesar(self, monto: int) -> ResultadoPago:
        _validar_monto(monto)
        if self._saldo < monto:
            return ResultadoPago(False, "", self.nombre, "Saldo insuficiente en la billetera")
        self._saldo -= monto
        self._ultimo_cargo = monto
        return ResultadoPago(
            True,
            f"BIL-{uuid4().hex[:8].upper()}",
            self.nombre,
            "Pago con billetera aprobado",
        )

    def anular(self, resultado: ResultadoPago) -> None:
        if resultado.aprobado and self._ultimo_cargo:
            self._saldo += self._ultimo_cargo
            self._ultimo_cargo = 0


class PagoTransferencia(MetodoPago):
    """Medio nuevo. No modifica las clases de pago que ya existían."""

    def __init__(self, numero_operacion: str, aprobado: bool = True):
        self._numero_operacion = texto_obligatorio(numero_operacion, "Número de operación")
        self._aprobado = booleano(aprobado, "La simulación de la transferencia")

    @property
    def nombre(self) -> str:
        return "Transferencia"

    def procesar(self, monto: int) -> ResultadoPago:
        _validar_monto(monto)
        if not self._aprobado:
            return ResultadoPago(
                False,
                self._numero_operacion,
                self.nombre,
                "La transferencia fue rechazada",
            )
        return ResultadoPago(True, self._numero_operacion, self.nombre, "Transferencia aprobada")
