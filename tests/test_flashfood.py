"""Reglas de negocio, persistencia y separación del modelo."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from flashfood.modelo.errores import PersistenciaError, ReglaNegocioError
from flashfood.modelo.pago import MetodoPago, PagoBilletera, PagoEfectivo, PagoTarjeta, PagoTransferencia
from flashfood.modelo.pedido import EstadoPedido, Pedido
from flashfood.modelo.producto import Bebida, Comida, Producto
from flashfood.modelo.sistema import FlashFood
from flashfood.persistencia.repositorio_json import RepositorioJSON


class OperacionBase(unittest.TestCase):
    def setUp(self):
        self._temporal = tempfile.TemporaryDirectory()
        self.sistema = FlashFood(RepositorioJSON(self._temporal.name))
        self.comida = self.sistema.registrar_producto("Comida", "Hamburguesa", 6500, 10, "Sándwich")
        self.bebida = self.sistema.registrar_producto("Bebida", "Bebida cola", 1500, 8, 350)
        self.cliente = self.sistema.registrar_cliente("Camila Soto", "+56911111111", "Av. Central 123", False)
        self.vip = self.sistema.registrar_cliente("Andrés Rojas", "+56922222222", "Los Aromos 45", True)
        self.repartidor = self.sistema.registrar_repartidor("Diego Muñoz", "Bicicleta")
        self.otro = self.sistema.registrar_repartidor("Marta López", "Moto")

    def tearDown(self):
        self._temporal.cleanup()

    def pedido_con(self, cliente_id: str, cantidades: tuple[tuple[str, int], ...]):
        pedido = self.sistema.crear_pedido(cliente_id)
        for producto_id, cantidad in cantidades:
            self.sistema.agregar_producto(pedido.id, producto_id, cantidad)
        return pedido


class ReglasTests(OperacionBase):
    def test_flujo_completo_y_liberacion(self):
        pedido = self.pedido_con(self.cliente.id, ((self.comida.id, 2), (self.bebida.id, 1)))
        self.assertEqual(pedido.subtotal, 14500)
        self.assertEqual(pedido.costo_despacho, 2000)
        self.assertEqual(pedido.total, 16500)
        self.sistema.pagar(pedido.id, PagoTarjeta())
        self.assertEqual(self.comida.stock, 8)
        self.assertEqual(self.bebida.stock, 7)
        self.sistema.preparar(pedido.id)
        self.sistema.asignar_repartidor(pedido.id, self.repartidor.id)
        self.assertFalse(self.repartidor.disponible)
        self.sistema.despachar(pedido.id)
        self.sistema.entregar(pedido.id)
        self.assertEqual(pedido.estado, EstadoPedido.ENTREGADO)
        self.assertEqual(
            [estado for estado in pedido.historial],
            [
                EstadoPedido.CREADO,
                EstadoPedido.PAGADO,
                EstadoPedido.EN_PREPARACION,
                EstadoPedido.EN_CAMINO,
                EstadoPedido.ENTREGADO,
            ],
        )
        self.assertTrue(self.repartidor.disponible)

    def test_no_vende_mas_que_el_stock_ni_lo_deja_negativo(self):
        pedido = self.sistema.crear_pedido(self.cliente.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.agregar_producto(pedido.id, self.comida.id, 11)
        self.sistema.agregar_producto(pedido.id, self.comida.id, 6)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.agregar_producto(pedido.id, self.comida.id, 5)
        self.assertEqual(self.comida.stock, 10)
        self.assertEqual(self.sistema.stock_disponible(self.comida.id), 4)

    def test_dos_pedidos_no_comprometen_el_mismo_stock(self):
        primero = self.pedido_con(self.cliente.id, ((self.comida.id, 7),))
        segundo = self.sistema.crear_pedido(self.vip.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.agregar_producto(segundo.id, self.comida.id, 4)
        self.sistema.agregar_producto(segundo.id, self.comida.id, 3)
        self.assertEqual(primero.cantidad_de(self.comida.id), 7)
        self.assertEqual(self.comida.stock, 10)

    def test_pago_rechazado_no_descuenta_y_permite_reintentar(self):
        pedido = self.pedido_con(self.cliente.id, ((self.comida.id, 2),))
        billetera = PagoBilletera(100)
        resultado = self.sistema.pagar(pedido.id, billetera)
        self.assertFalse(resultado.aprobado)
        self.assertEqual(billetera.saldo, 100)
        self.assertEqual(pedido.estado, EstadoPedido.CREADO)
        self.assertIsNone(pedido.pago)
        self.assertEqual(self.comida.stock, 10)
        self.assertTrue(self.sistema.pagar(pedido.id, PagoTarjeta()).aprobado)
        self.assertEqual(self.comida.stock, 8)

    def test_no_se_paga_dos_veces_ni_se_descuenta_dos_veces(self):
        pedido = self.pedido_con(self.cliente.id, ((self.comida.id, 2),))
        billetera = PagoBilletera(40000)
        self.sistema.pagar(pedido.id, billetera)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.pagar(pedido.id, billetera)
        self.assertEqual(billetera.saldo, 40000 - pedido.total)
        self.assertEqual(self.comida.stock, 8)

    def test_efectivo_insuficiente_no_confirma(self):
        pedido = self.pedido_con(self.cliente.id, ((self.bebida.id, 1),))
        resultado = self.sistema.pagar(pedido.id, PagoEfectivo(100))
        self.assertFalse(resultado.aprobado)
        self.assertEqual(self.bebida.stock, 8)
        aprobado = self.sistema.pagar(pedido.id, PagoEfectivo(pedido.total + 500))
        self.assertIn("500", aprobado.mensaje)
        self.assertEqual(self.bebida.stock, 7)

    def test_cancelar_restituye_una_sola_vez_y_libera_repartidor(self):
        pedido = self.pedido_con(self.cliente.id, ((self.comida.id, 4),))
        self.sistema.cancelar(pedido.id)
        self.assertEqual(self.comida.stock, 10)
        otro = self.pedido_con(self.cliente.id, ((self.comida.id, 4),))
        self.sistema.pagar(otro.id, PagoTarjeta())
        self.sistema.preparar(otro.id)
        self.sistema.asignar_repartidor(otro.id, self.repartidor.id)
        self.sistema.cancelar(otro.id)
        self.assertEqual(self.comida.stock, 10)
        self.assertTrue(self.repartidor.disponible)
        self.assertTrue(otro.stock_restituido)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.cancelar(otro.id)
        self.assertEqual(self.comida.stock, 10)

    def test_entregado_es_final_y_no_se_saltan_estados(self):
        pedido = self.pedido_con(self.cliente.id, ((self.comida.id, 1),))
        with self.assertRaises(ReglaNegocioError):
            self.sistema.preparar(pedido.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.asignar_repartidor(pedido.id, self.repartidor.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.entregar(pedido.id)
        self.sistema.pagar(pedido.id, PagoTarjeta())
        self.sistema.preparar(pedido.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.despachar(pedido.id)
        self.sistema.asignar_repartidor(pedido.id, self.repartidor.id)
        self.sistema.despachar(pedido.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.cancelar(pedido.id)
        self.sistema.entregar(pedido.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.cancelar(pedido.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.entregar(pedido.id)

    def test_repartidor_no_tiene_dos_entregas(self):
        primero = self.pedido_con(self.cliente.id, ((self.comida.id, 1),))
        segundo = self.pedido_con(self.vip.id, ((self.bebida.id, 1),))
        for pedido in (primero, segundo):
            self.sistema.pagar(pedido.id, PagoTarjeta())
            self.sistema.preparar(pedido.id)
        self.sistema.asignar_repartidor(primero.id, self.repartidor.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.asignar_repartidor(segundo.id, self.repartidor.id)
        self.sistema.despachar(primero.id)
        self.sistema.entregar(primero.id)
        self.sistema.asignar_repartidor(segundo.id, self.repartidor.id)
        self.assertEqual(segundo.repartidor_id, self.repartidor.id)

    def test_vip_hora_punta_y_lluvia_quedan_congelados(self):
        self.sistema.definir_condiciones(True, True)
        pedido = self.pedido_con(self.vip.id, ((self.comida.id, 2),))
        self.assertEqual(pedido.subtotal, 13000)
        self.assertEqual(pedido.descuento, 1300)
        self.assertEqual(pedido.costo_despacho, 3500)
        self.assertEqual(pedido.total, 15200)
        self.sistema.definir_condiciones(False, False)
        self.assertEqual(pedido.total, 15200)
        normal = self.sistema.crear_pedido(self.cliente.id)
        self.assertEqual(normal.costo_despacho, Pedido.DESPACHO_BASE)
        self.assertEqual(normal.descuento, 0)

    def test_transferencia_sin_cambiar_las_otras_clases(self):
        pedido = self.pedido_con(self.cliente.id, ((self.bebida.id, 1),))
        rechazo = self.sistema.pagar(pedido.id, PagoTransferencia("OP-1", False))
        self.assertFalse(rechazo.aprobado)
        self.assertEqual(self.bebida.stock, 8)
        aprobado = self.sistema.pagar(pedido.id, PagoTransferencia("OP-1", True))
        self.assertTrue(aprobado.aprobado)
        self.assertEqual(aprobado.referencia, "OP-1")
        self.assertIsInstance(PagoTransferencia("OP-2"), MetodoPago)

    def test_el_precio_de_la_linea_no_cambia_si_cambia_el_catalogo(self):
        pedido = self.pedido_con(self.cliente.id, ((self.comida.id, 1),))
        self.sistema.editar_producto(self.comida.id, "Hamburguesa doble", 9000, 10, "Sándwich")
        self.assertEqual(pedido.detalles[0].precio_unitario, 6500)
        self.assertEqual(pedido.detalles[0].nombre, "Hamburguesa")

    def test_no_edita_stock_bajo_lo_comprometido_ni_elimina_producto_en_uso(self):
        self.pedido_con(self.cliente.id, ((self.comida.id, 4),))
        with self.assertRaises(ReglaNegocioError):
            self.sistema.editar_producto(self.comida.id, "Hamburguesa", 6500, 3, "Sándwich")
        with self.assertRaises(ReglaNegocioError):
            self.sistema.eliminar_producto(self.comida.id)
        self.sistema.editar_producto(self.comida.id, "Hamburguesa", 6500, 4, "Sándwich")
        self.assertEqual(self.comida.stock, 4)

    def test_si_falla_el_descuento_no_queda_pago_ni_stock_a_medias(self):
        pedido = self.pedido_con(self.cliente.id, ((self.comida.id, 1), (self.bebida.id, 1)))
        billetera = PagoBilletera(50000)
        original = self.bebida.descontar

        def falla(cantidad):
            raise ReglaNegocioError("fallo de inventario")

        self.bebida.descontar = falla
        with self.assertRaises(ReglaNegocioError):
            self.sistema.pagar(pedido.id, billetera)
        self.bebida.descontar = original
        self.assertEqual(pedido.estado, EstadoPedido.CREADO)
        self.assertIsNone(pedido.pago)
        self.assertEqual(self.comida.stock, 10)
        self.assertEqual(self.bebida.stock, 8)
        self.assertEqual(billetera.saldo, 50000)

    def test_validaciones_y_pilares(self):
        with self.assertRaises(TypeError):
            Producto("p", "X", 1, 1)
        with self.assertRaises(TypeError):
            MetodoPago()
        with self.assertRaises(ReglaNegocioError):
            Comida("p", " ", 1000, 1, "Horno")
        with self.assertRaises(ReglaNegocioError):
            Bebida("b", "Agua", 1000, 1, 0)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.registrar_producto("Comida", "Hamburguesa", 1000, 1, "Otra")
        for precio in (0, -1, True, 1.5):
            with self.assertRaises(ReglaNegocioError):
                Comida("p", "Pizza", precio, 1, "Horno")
        pedido = self.sistema.crear_pedido(self.cliente.id)
        with self.assertRaises(AttributeError):
            pedido.estado = EstadoPedido.ENTREGADO
        self.assertIsInstance(pedido.detalles, tuple)
        self.assertIsInstance(pedido.historial, tuple)

    def test_crud_de_cliente_y_repartidor(self):
        self.sistema.editar_cliente(self.cliente.id, "Camila Pérez", "+56911111111", "Nueva 9", True)
        cliente = self.sistema.obtener_cliente(self.cliente.id)
        self.assertEqual(cliente.nombre, "Camila Pérez")
        self.assertTrue(cliente.es_vip)
        suelto = self.sistema.registrar_cliente("Sin pedidos", "+56933333333", "Calle 4", False)
        self.sistema.eliminar_cliente(suelto.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.obtener_cliente(suelto.id)
        self.pedido_con(self.cliente.id, ((self.comida.id, 1),))
        with self.assertRaises(ReglaNegocioError):
            self.sistema.eliminar_cliente(self.cliente.id)

        self.sistema.editar_repartidor(self.otro.id, "Marta Díaz", "Auto")
        self.assertEqual(self.sistema.obtener_repartidor(self.otro.id).vehiculo, "Auto")
        self.sistema.eliminar_repartidor(self.otro.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.obtener_repartidor(self.otro.id)
        pedido = self.pedido_con(self.cliente.id, ((self.bebida.id, 1),))
        self.sistema.pagar(pedido.id, PagoTarjeta())
        self.sistema.preparar(pedido.id)
        self.sistema.asignar_repartidor(pedido.id, self.repartidor.id)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.eliminar_repartidor(self.repartidor.id)

    def test_acciones_siguen_al_estado(self):
        pedido = self.pedido_con(self.cliente.id, ((self.comida.id, 1),))
        self.assertTrue(self.sistema.acciones(pedido.id)["puede_pagar"])
        self.assertFalse(self.sistema.acciones(pedido.id)["puede_preparar"])
        self.sistema.pagar(pedido.id, PagoTarjeta())
        self.assertTrue(self.sistema.acciones(pedido.id)["puede_preparar"])
        self.assertTrue(self.sistema.acciones(pedido.id)["puede_cancelar"])
        self.sistema.preparar(pedido.id)
        self.assertTrue(self.sistema.acciones(pedido.id)["puede_asignar"])
        self.assertFalse(self.sistema.acciones(pedido.id)["puede_despachar"])


class PersistenciaTests(OperacionBase):
    def test_recarga_sin_volver_a_descontar(self):
        pedido = self.pedido_con(self.cliente.id, ((self.comida.id, 2),))
        self.sistema.pagar(pedido.id, PagoTarjeta())
        self.sistema.preparar(pedido.id)
        self.sistema.asignar_repartidor(pedido.id, self.repartidor.id)
        recuperado = FlashFood(RepositorioJSON(self._temporal.name))
        pedido_cargado = recuperado.obtener_pedido(pedido.id)
        self.assertEqual(pedido_cargado.estado, EstadoPedido.EN_PREPARACION)
        self.assertEqual(recuperado.obtener_producto(self.comida.id).stock, 8)
        self.assertFalse(recuperado.obtener_repartidor(self.repartidor.id).disponible)
        with self.assertRaises(ReglaNegocioError):
            recuperado.pagar(pedido.id, PagoTarjeta())
        self.assertEqual(recuperado.obtener_producto(self.comida.id).stock, 8)

    def test_archivo_danado_no_cierra_y_no_se_sobrescribe(self):
        ruta = Path(self._temporal.name) / "productos.json"
        ruta.write_text("{esto no es json", encoding="utf-8")
        sistema = FlashFood(RepositorioJSON(self._temporal.name))
        self.assertTrue(sistema.advertencias)
        self.assertEqual(sistema.listar_productos(), ())
        with self.assertRaises(PersistenciaError):
            sistema.registrar_cliente("Ana", "+56911112222", "Calle 1", False)
        self.assertTrue(ruta.with_name("productos.json.bak").exists())

    def test_datos_de_ejemplo(self):
        raiz = Path(__file__).resolve().parents[1] / "data"
        sistema = FlashFood(RepositorioJSON(raiz))
        self.assertEqual(sistema.obtener_producto("prod-hamburguesa").precio, 6500)
        self.assertTrue(sistema.obtener_cliente("cli-andres").es_vip)
        self.assertEqual(sistema.obtener_producto("prod-cola").detalle, "350 ml")
        self.assertEqual(sistema.listar_pedidos(), ())


class ControladorTests(unittest.TestCase):
    def setUp(self):
        self._temporal = tempfile.TemporaryDirectory()
        from flashfood.controladores.controlador import Controlador

        self.controlador = Controlador(self._temporal.name)

    def tearDown(self):
        self._temporal.cleanup()

    def test_rechaza_texto_que_no_es_entero(self):
        for precio in ("", "abc", "1.5", "6.500", "-5"):
            with self.assertRaises(ReglaNegocioError):
                self.controlador.registrar_producto("Comida", "Pizza", precio, "1", "Horno")
        with self.assertRaises(ReglaNegocioError):
            self.controlador.registrar_producto("Bebida", "Agua", "1000", "1", "medio")
        self.controlador.registrar_producto("Comida", "Pizza", "4500", "0", "Horno")
        self.assertEqual(self.controlador.listar_productos()[0].stock, 0)


class SeparacionTests(unittest.TestCase):
    def test_modelo_persistencia_y_controlador_no_importan_tkinter_ni_qt(self):
        raiz = Path(__file__).resolve().parents[1] / "src" / "flashfood"
        for carpeta in ("modelo", "persistencia", "controladores"):
            for archivo in (raiz / carpeta).glob("*.py"):
                texto = archivo.read_text(encoding="utf-8")
                self.assertNotIn("tkinter", texto, archivo.name)
                self.assertNotIn("PySide6", texto, archivo.name)
        for nombre in ("domain.py", "application.py", "infrastructure.py", "desktop.py", "ejemplo.py", "interfaz.py"):
            self.assertFalse((raiz / nombre).exists(), nombre)


class InterfazTests(unittest.TestCase):
    def setUp(self):
        try:
            import tkinter as tk

            sonda = tk.Tk()
            sonda.withdraw()
            sonda.destroy()
        except Exception as error:
            self.skipTest(f"Tk no disponible: {error}")
        self._temporal = tempfile.TemporaryDirectory()
        from flashfood.controladores.controlador import Controlador
        from flashfood.vista.aplicacion import Aplicacion
        import flashfood.vista.comun as comun
        import flashfood.vista.productos as productos
        import flashfood.vista.clientes as clientes
        import flashfood.vista.pedidos as pedidos
        import flashfood.vista.pagos as pagos
        import flashfood.vista.repartidores as repartidores
        import flashfood.vista.seguimiento as seguimiento

        self.comun = comun
        self.errores = comun.mostrar_error = MagicMock()
        for modulo in (productos, clientes, pedidos, pagos, repartidores, seguimiento):
            modulo.informar = MagicMock()
            modulo.mostrar_error = MagicMock()
            if hasattr(modulo, "pedir_confirmacion"):
                modulo.pedir_confirmacion = MagicMock(return_value=True)
        self.app = Aplicacion(Controlador(self._temporal.name))
        self.app.withdraw()
        self.app.update_idletasks()

    def tearDown(self):
        self.app.destroy()
        self._temporal.cleanup()

    def test_flujo_desde_las_pantallas(self):
        self.app._botones_nav["clientes"].invoke()
        self.assertIs(self.app._actual, self.app._pantallas["clientes"])
        self.app._botones_nav["productos"].invoke()
        self.assertIs(self.app._actual, self.app._pantallas["productos"])
        productos = self.app._pantallas["productos"]
        self.app.mostrar("productos")
        productos.tipo.set("Comida")
        productos.nombre.set("Empanada")
        productos.precio.set("3000")
        productos.stock.set("5")
        productos.extra.set("Horno")
        productos.registrar()
        self.assertEqual(len(productos.tabla.get_children()), 1)
        producto_id = productos.tabla.get_children()[0]

        clientes = self.app._pantallas["clientes"]
        self.app.mostrar("clientes")
        clientes.nombre.set("Ana")
        clientes.telefono.set("987654321")
        clientes.direccion.set("Calle 1")
        clientes.es_vip.set(True)
        clientes.registrar()
        cliente_id = clientes.tabla.get_children()[0]

        repartidores = self.app._pantallas["repartidores"]
        self.app.mostrar("repartidores")
        repartidores.nombre.set("Luis")
        repartidores.vehiculo.set("Moto")
        repartidores.registrar()

        pedidos = self.app._pantallas["pedidos"]
        self.app.mostrar("pedidos")
        pedidos.crear()
        pedidos.cantidad.set("9")
        pedidos.agregar()
        self.errores.assert_called()
        self.assertEqual(self.app.controlador.obtener_producto(producto_id).stock, 5)
        pedidos.cantidad.set("2")
        pedidos.agregar()
        pedido_id = pedidos.tabla.get_children()[0]
        self.assertEqual(self.app.controlador.obtener_pedido(pedido_id).detalles[0].cantidad, 2)
        self.assertEqual(self.app.controlador.obtener_pedido(pedido_id).descuento, 600)

        pagos = self.app._pantallas["pagos"]
        self.app.mostrar("pagos")
        pagos.medio.set("Tarjeta")
        pagos.mostrar_campos()
        pagos.rechazar_tarjeta.set(True)
        pagos.procesar()
        self.assertEqual(self.app.controlador.obtener_producto(producto_id).stock, 5)
        pagos.rechazar_tarjeta.set(False)
        pagos.procesar()
        self.assertEqual(self.app.controlador.obtener_producto(producto_id).stock, 3)

        seguimiento = self.app._pantallas["seguimiento"]
        self.app.mostrar("seguimiento")
        seguimiento.tabla.selection_set(pedido_id)
        seguimiento.al_seleccionar()
        seguimiento.preparar()
        self.app.mostrar("repartidores")
        repartidores.asignar()
        self.app.mostrar("seguimiento")
        seguimiento.tabla.selection_set(pedido_id)
        seguimiento.al_seleccionar()
        seguimiento.despachar()
        seguimiento.entregar()
        self.assertEqual(self.app.controlador.obtener_pedido(pedido_id).estado, EstadoPedido.ENTREGADO)
        self.assertTrue(self.app.controlador.obtener_repartidor(repartidores.tabla.get_children()[0]).disponible)

        self.app.mostrar("detalle")
        self.app._pantallas["detalle"].mostrar()
        self.assertIn("Entregado", self.app._pantallas["detalle"].resumen.cget("text"))
        self.assertEqual(cliente_id, self.app.controlador.listar_clientes()[0].id)

        guardado = json.loads((Path(self._temporal.name) / "pedidos.json").read_text(encoding="utf-8"))
        self.assertEqual(guardado[0]["estado"], "ENTREGADO")


if __name__ == "__main__":
    unittest.main()
