"""Entidades y reglas del negocio. Importes en pesos chilenos enteros."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class ReglaNegocioError(ValueError):
    """Una operación viola las reglas de FlashFood."""


class EstadoPedido(Enum):
    RECIBIDO = "Recibido"
    PAGADO = "Pagado"
    ASIGNADO = "Asignado"
    EN_CAMINO = "En camino"
    ENTREGADO = "Entregado"


def texto_obligatorio(valor: str, campo: str) -> None:
    if not isinstance(valor, str) or not valor.strip():
        raise ReglaNegocioError(f"{campo} es obligatorio")


@dataclass(frozen=True)
class Persona:
    id: str
    nombre: str

    def __post_init__(self):
        texto_obligatorio(self.id, "Identificador")
        texto_obligatorio(self.nombre, "Nombre")


@dataclass(frozen=True)
class Cliente(Persona):
    direccion: str

    def __post_init__(self):
        super().__post_init__()
        texto_obligatorio(self.direccion, "Dirección")


@dataclass(frozen=True)
class Repartidor(Persona):
    vehiculo: str

    def __post_init__(self):
        super().__post_init__()
        texto_obligatorio(self.vehiculo, "Vehículo")


@dataclass(frozen=True)
class Producto:
    nombre: str
    precio: int

    def __post_init__(self):
        texto_obligatorio(self.nombre, "Producto")
        if type(self.precio) is not int or self.precio <= 0:
            raise ReglaNegocioError("El precio debe ser un entero positivo en CLP")


@dataclass(frozen=True)
class ItemPedido:
    producto: Producto
    cantidad: int

    def __post_init__(self):
        if type(self.cantidad) is not int or self.cantidad <= 0:
            raise ReglaNegocioError("La cantidad debe ser un entero positivo")

    @property
    def subtotal(self) -> int:
        return self.producto.precio * self.cantidad


@dataclass(frozen=True)
class ResultadoPago:
    aprobado: bool
    referencia: str


class MedioPago(ABC):
    """Abstracción: cualquier medio de pago respeta este contrato."""

    @abstractmethod
    def cobrar(self, monto: int) -> ResultadoPago:
        """Simula un cobro; nunca procesa dinero real."""


class PagoTarjeta(MedioPago):
    def __init__(self, aprobado: bool = True):
        self._aprobado = aprobado

    def cobrar(self, monto: int) -> ResultadoPago:
        if type(monto) is not int or monto <= 0:
            raise ReglaNegocioError("Monto inválido")
        return ResultadoPago(self._aprobado, f"TAR-{uuid4()}")


class PagoBilletera(MedioPago):
    def __init__(self, saldo: int):
        if type(saldo) is not int or saldo < 0:
            raise ReglaNegocioError("Saldo inválido")
        self._saldo = saldo

    @property
    def saldo(self) -> int:
        return self._saldo

    def cobrar(self, monto: int) -> ResultadoPago:
        if type(monto) is not int or monto <= 0:
            raise ReglaNegocioError("Monto inválido")
        aprobado = self._saldo >= monto
        if aprobado:
            self._saldo -= monto
        return ResultadoPago(aprobado, f"BIL-{uuid4()}")


class Pedido:
    """Agregado: encapsula sus ítems, pago y transiciones de estado.

    El prefijo _ es una convención de acceso interno, no seguridad.
    La API pública expone propiedades sin setters y tuplas inmutables.
    """

    def __init__(self, cliente: Cliente, plataforma: str, items: tuple[ItemPedido, ...]):
        texto_obligatorio(plataforma, "Plataforma")
        if not items or not all(isinstance(i, ItemPedido) for i in items):
            raise ReglaNegocioError("El pedido debe contener ítems válidos")
        self._id = str(uuid4())
        self._cliente = cliente
        self._plataforma = plataforma
        self._items = tuple(items)
        self._estado = EstadoPedido.RECIBIDO
        self._repartidor = None
        self._pago = None
        self._historial = [self._estado]

    @property
    def id(self): return self._id

    @property
    def cliente(self): return self._cliente

    @property
    def plataforma(self): return self._plataforma

    @property
    def items(self): return self._items

    @property
    def total(self): return sum(item.subtotal for item in self._items)

    @property
    def estado(self): return self._estado

    @property
    def repartidor(self): return self._repartidor

    @property
    def pago(self): return self._pago

    @property
    def historial(self): return tuple(self._historial)

    def _exigir(self, estado: EstadoPedido):
        if self._estado is not estado:
            raise ReglaNegocioError(f"Se requiere {estado.value}; estado actual: {self.estado.value}")

    def _cambiar(self, estado: EstadoPedido):
        self._estado = estado
        self._historial.append(estado)

    def pagar(self, medio: MedioPago) -> ResultadoPago:
        self._exigir(EstadoPedido.RECIBIDO)
        resultado = medio.cobrar(self.total)  # Polimorfismo: no pregunta qué clase es.
        if resultado.aprobado:
            self._pago = resultado
            self._cambiar(EstadoPedido.PAGADO)
        return resultado

    def asignar(self, repartidor: Repartidor):
        self._exigir(EstadoPedido.PAGADO)
        if not isinstance(repartidor, Repartidor):
            raise ReglaNegocioError("Se requiere un repartidor válido")
        self._repartidor = repartidor
        self._cambiar(EstadoPedido.ASIGNADO)

    def iniciar_entrega(self):
        self._exigir(EstadoPedido.ASIGNADO)
        self._cambiar(EstadoPedido.EN_CAMINO)

    def entregar(self):
        self._exigir(EstadoPedido.EN_CAMINO)
        self._cambiar(EstadoPedido.ENTREGADO)
