from flashfood.application import RepositorioPedidos
from flashfood.domain import Pedido, ReglaNegocioError


class RepositorioEnMemoria(RepositorioPedidos):
    """Los datos se pierden al cerrar. No ofrece concurrencia ni transacciones."""
    def __init__(self):
        self._pedidos: dict[str, Pedido] = {}

    def guardar(self, pedido):
        self._pedidos[pedido.id] = pedido

    def obtener(self, id_pedido):
        try:
            return self._pedidos[id_pedido]
        except KeyError as error:
            raise ReglaNegocioError("Pedido inexistente") from error

    def listar(self):
        return tuple(self._pedidos.values())
