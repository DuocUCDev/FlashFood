"""Casos de uso y contratos; compartidos por consola y escritorio."""
from abc import ABC, abstractmethod
from flashfood.domain import Cliente, ItemPedido, MedioPago, Pedido, Repartidor, ReglaNegocioError


class RepositorioPedidos(ABC):
    @abstractmethod
    def guardar(self, pedido: Pedido) -> None: ...

    @abstractmethod
    def obtener(self, id_pedido: str) -> Pedido: ...

    @abstractmethod
    def listar(self) -> tuple[Pedido, ...]: ...


class PlataformaComida(ABC):
    @property
    @abstractmethod
    def nombre(self) -> str: ...

    @abstractmethod
    def recibir(self, cliente: Cliente, items: tuple[ItemPedido, ...]) -> Pedido: ...


class PlataformaSimulada(PlataformaComida):
    """Adaptador didáctico; no representa una integración externa real."""
    def __init__(self, nombre: str):
        if not nombre.strip():
            raise ReglaNegocioError("Nombre de plataforma obligatorio")
        self._nombre = nombre

    @property
    def nombre(self): return self._nombre

    def recibir(self, cliente, items):
        return Pedido(cliente, self.nombre, items)


class ServicioPedidos:
    def __init__(self, repositorio: RepositorioPedidos):
        self._repositorio = repositorio  # Inyección de dependencias.

    def recibir(self, plataforma: PlataformaComida, cliente: Cliente, items: tuple[ItemPedido, ...]) -> Pedido:
        pedido = plataforma.recibir(cliente, items)
        self._repositorio.guardar(pedido)
        return pedido

    def listar(self): return self._repositorio.listar()

    def pagar(self, id_pedido: str, medio: MedioPago):
        pedido = self._repositorio.obtener(id_pedido)
        resultado = pedido.pagar(medio)
        self._repositorio.guardar(pedido)
        return resultado

    def asignar(self, id_pedido: str, repartidor: Repartidor):
        # En esta versión un repartidor atiende un pedido activo a la vez.
        from flashfood.domain import EstadoPedido
        if any(p.repartidor == repartidor and p.estado in (EstadoPedido.ASIGNADO, EstadoPedido.EN_CAMINO)
               for p in self.listar()):
            raise ReglaNegocioError("El repartidor ya tiene un pedido activo")
        pedido = self._repositorio.obtener(id_pedido)
        pedido.asignar(repartidor)
        self._repositorio.guardar(pedido)

    def iniciar_entrega(self, id_pedido: str):
        pedido = self._repositorio.obtener(id_pedido)
        pedido.iniciar_entrega()
        self._repositorio.guardar(pedido)

    def entregar(self, id_pedido: str):
        pedido = self._repositorio.obtener(id_pedido)
        pedido.entregar()
        self._repositorio.guardar(pedido)
