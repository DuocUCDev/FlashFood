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
    pizza = Producto("Pizza", 8000, 10)
    cocacola = Producto("CocaCoca", 2000, 50)
    item1 = ItemPedido(pizza, 2)
    item2 = ItemPedido(cocacola, 1)

    # El pedido contiene un cliente y sus items
    pedido = Pedido(
        cliente=ana,
        plataforma="UberEats",
        items=(item1,item2)
    )

    tarjeta = PagoTarjeta()
    juanito = Repartidor("R001", "Juanito", "Motochorro")
    pedido.pagar(tarjeta)
    pedido.asignar(juanito)

    print("Cliente: ", pedido.cliente.nombre)
    print("Repartidor: ", pedido.repartidor)
    print("Total: ", pedido.total)
    print("Estado incial: ", pedido.estado)
    print("Historial estado: ", pedido.historial)


if __name__ == "__main__":
    main()