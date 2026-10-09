import unittest
from flashfood.domain import *
from flashfood.application import PlataformaSimulada, ServicioPedidos
from flashfood.infrastructure import RepositorioEnMemoria


class FlashFoodTests(unittest.TestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()
        self.servicio = ServicioPedidos(self.repo)
        self.cliente = Cliente('C1', 'Ana', 'Calle 123')
        self.items = (ItemPedido(Producto('Pizza', 8000), 2),)
        self.pedido = self.servicio.recibir(PlataformaSimulada('FoodApp'), self.cliente, self.items)
        self.repartidor = Repartidor('R1', 'Luis', 'Moto')

    def test_flujo_completo(self):
        self.assertEqual(self.pedido.total, 16000)
        self.servicio.pagar(self.pedido.id, PagoTarjeta())
        self.servicio.asignar(self.pedido.id, self.repartidor)
        self.servicio.iniciar_entrega(self.pedido.id)
        self.servicio.entregar(self.pedido.id)
        self.assertEqual(self.pedido.historial, tuple(EstadoPedido))
        self.assertEqual(self.pedido.repartidor, self.repartidor)
        self.assertTrue(self.pedido.pago.aprobado)

    def test_rechazo_permite_reintentar(self):
        self.assertFalse(self.servicio.pagar(self.pedido.id, PagoTarjeta(False)).aprobado)
        self.assertEqual(self.pedido.estado, EstadoPedido.RECIBIDO)
        self.assertIsNone(self.pedido.pago)
        self.assertTrue(self.servicio.pagar(self.pedido.id, PagoTarjeta()).aprobado)

    def test_billetera_no_descuenta_si_no_alcanza(self):
        billetera = PagoBilletera(100)
        self.assertFalse(self.pedido.pagar(billetera).aprobado)
        self.assertEqual(billetera.saldo, 100)

    def test_no_hay_doble_cobro(self):
        billetera = PagoBilletera(40000)
        self.pedido.pagar(billetera)
        with self.assertRaises(ReglaNegocioError): self.pedido.pagar(billetera)
        self.assertEqual(billetera.saldo, 24000)

    def test_transiciones_invalidas(self):
        for accion in [lambda: self.pedido.asignar(self.repartidor), self.pedido.iniciar_entrega, self.pedido.entregar]:
            with self.assertRaises(ReglaNegocioError): accion()
        self.pedido.pagar(PagoTarjeta())
        self.pedido.asignar(self.repartidor)
        with self.assertRaises(ReglaNegocioError): self.pedido.entregar()
        self.pedido.iniciar_entrega()
        self.pedido.entregar()
        with self.assertRaises(ReglaNegocioError): self.pedido.entregar()

    def test_repartidor_ocupado_y_liberado(self):
        otro = self.servicio.recibir(PlataformaSimulada('DeliveryWeb'), self.cliente, self.items)
        self.servicio.pagar(self.pedido.id, PagoTarjeta())
        self.servicio.pagar(otro.id, PagoTarjeta())
        self.servicio.asignar(self.pedido.id, self.repartidor)
        with self.assertRaises(ReglaNegocioError): self.servicio.asignar(otro.id, self.repartidor)
        self.servicio.iniciar_entrega(self.pedido.id)
        self.servicio.entregar(self.pedido.id)
        self.servicio.asignar(otro.id, self.repartidor)
        self.assertEqual(otro.estado, EstadoPedido.ASIGNADO)

    def test_validaciones(self):
        for valor in [0, -1, True, 1.5]:
            with self.assertRaises(ReglaNegocioError): Producto('Pizza', valor)
            with self.assertRaises(ReglaNegocioError): ItemPedido(Producto('Pizza', 10), valor)
        with self.assertRaises(ReglaNegocioError): Pedido(self.cliente, 'App', ())
        with self.assertRaises(ReglaNegocioError): Cliente('C', ' ', 'Calle')
        with self.assertRaises(ReglaNegocioError): self.repo.obtener('inexistente')

    def test_encapsulacion(self):
        with self.assertRaises(AttributeError): self.pedido.estado = EstadoPedido.ENTREGADO
        self.assertIsInstance(self.pedido.items, tuple)
        self.assertIsInstance(self.pedido.historial, tuple)

    def test_abstraccion_no_se_instancia(self):
        with self.assertRaises(TypeError): MedioPago()


if __name__ == '__main__':
    unittest.main()
