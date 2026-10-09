from flashfood.application import PlataformaSimulada, ServicioPedidos
from flashfood.domain import Cliente, ItemPedido, PagoTarjeta, Producto, Repartidor
from flashfood.infrastructure import RepositorioEnMemoria


def main():
    servicio = ServicioPedidos(RepositorioEnMemoria())
    pedido = servicio.recibir(PlataformaSimulada("FoodApp"),
        Cliente("C1", "Camila", "Av. Central 123"),
        (ItemPedido(Producto("Hamburguesa", 6500), 2),))
    print(f"Pedido {pedido.id}: ${pedido.total:,} CLP — {pedido.estado.value}")
    servicio.pagar(pedido.id, PagoTarjeta())
    servicio.asignar(pedido.id, Repartidor("R1", "Diego", "Bicicleta"))
    servicio.iniciar_entrega(pedido.id)
    servicio.entregar(pedido.id)
    print(" → ".join(estado.value for estado in pedido.historial))


if __name__ == "__main__":
    main()
