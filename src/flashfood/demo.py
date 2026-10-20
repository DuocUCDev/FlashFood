"""Recorrido del flujo completo sin interfaz gráfica."""

from tempfile import TemporaryDirectory

from flashfood.modelo.pago import PagoEfectivo, PagoTarjeta
from flashfood.modelo.pedido import EstadoPedido
from flashfood.modelo.sistema import FlashFood
from flashfood.persistencia.repositorio_json import RepositorioJSON


def main() -> None:
    with TemporaryDirectory() as carpeta:
        sistema = FlashFood(RepositorioJSON(carpeta))
        sistema.definir_condiciones(hora_punta=True, lluvia=False)
        hamburguesa = sistema.registrar_producto("Comida", "Hamburguesa", 6500, 10, "Sándwich")
        bebida = sistema.registrar_producto("Bebida", "Bebida cola", 1500, 20, 350)
        cliente = sistema.registrar_cliente("Camila Soto", "+56911111111", "Av. Central 123", False)
        repartidor = sistema.registrar_repartidor("Diego Muñoz", "Bicicleta")
        pedido = sistema.crear_pedido(cliente.id)
        sistema.agregar_producto(pedido.id, hamburguesa.id, 2)
        sistema.agregar_producto(pedido.id, bebida.id, 1)
        print(f"Pedido {pedido.id}: total ${pedido.total} — {pedido.estado.etiqueta}")
        rechazo = sistema.pagar(pedido.id, PagoTarjeta(False))
        if rechazo.aprobado or hamburguesa.stock != 10:
            raise SystemExit("Un pago rechazado no debe confirmar ni descontar stock")
        print(f"Pago rechazado: {rechazo.mensaje}")
        sistema.pagar(pedido.id, PagoEfectivo(pedido.total))
        sistema.preparar(pedido.id)
        sistema.asignar_repartidor(pedido.id, repartidor.id)
        sistema.despachar(pedido.id)
        sistema.entregar(pedido.id)
        print(pedido.historial_texto())
        if pedido.estado is not EstadoPedido.ENTREGADO or not repartidor.disponible:
            raise SystemExit("La entrega debe cerrar el pedido y liberar al repartidor")
        if hamburguesa.stock != 8 or bebida.stock != 19:
            raise SystemExit("El stock descontado no coincide con el pedido")
    print("Flujo completo verificado.")


if __name__ == "__main__":
    main()
