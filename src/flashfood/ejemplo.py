from flashfood.domain import (
    Cliente,
    Producto,
    ItemPedido,
    Pedido,
    PagoTarjeta,
    Repartidor
)


def main():
    # Crear objeto 
    ana = Cliente("C1", "Ana", "Av. Principal 100")
    pizza = Producto("Pizza", 8000)
    cocacola = Producto("CocaCoca", 2000)
    item1 = ItemPedido(pizza, 2)
    item2 = ItemPedido(cocacola, 1)

    # El pedido contiene un cliente y sus items
    pedido = Pedido(
        cliente=ana,
        plataforma="UberEats",
        items=(item1,item2)
    )

    print("Cliente: ", pedido.cliente.nombre)
    print("Total: ", pedido.total)
    print("Estado incial: ", pedido.estado)


if __name__ == "__main__":
    main()