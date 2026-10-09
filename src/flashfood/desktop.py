"""Vista inicial: delega todas las reglas en ServicioPedidos."""
import sys
from flashfood.application import PlataformaSimulada, ServicioPedidos
from flashfood.domain import Cliente, EstadoPedido, ItemPedido, PagoBilletera, PagoTarjeta, Producto, Repartidor, ReglaNegocioError
from flashfood.infrastructure import RepositorioEnMemoria


def main():
    try:
        from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox
    except ImportError:
        raise SystemExit('Instala la interfaz con: python -m pip install -e ".[desktop]"')

    class Ventana(QWidget):
        def __init__(self):
            super().__init__()
            self.servicio = ServicioPedidos(RepositorioEnMemoria())
            self.pedido = None
            self.setWindowTitle("FlashFood — laboratorio POO")
            self.resize(520, 320)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Pedido de ejemplo: 2 hamburguesas de $6.500 CLP"))
            self.plataforma = QComboBox()
            self.plataforma.addItems(["FoodApp", "DeliveryWeb"])
            layout.addWidget(self.plataforma)
            self.medio = QComboBox()
            self.medio.addItems(["Tarjeta aprobada", "Tarjeta rechazada", "Billetera $20.000", "Billetera $1.000"])
            layout.addWidget(self.medio)
            self.resumen = QLabel()
            layout.addWidget(self.resumen)
            self.botones = {}
            for texto, accion in [("Crear pedido", self.crear), ("Pagar", self.pagar),
                    ("Asignar repartidor", self.asignar), ("Iniciar entrega", self.iniciar), ("Entregar", self.entregar)]:
                boton = QPushButton(texto)
                boton.clicked.connect(lambda checked=False, fn=accion: self.ejecutar(fn))
                layout.addWidget(boton)
                self.botones[texto] = boton
            self.actualizar()

        def ejecutar(self, accion):
            try:
                accion()
            except ReglaNegocioError as error:
                QMessageBox.warning(self, "Regla de negocio", str(error))
            self.actualizar()

        def crear(self):
            self.pedido = self.servicio.recibir(PlataformaSimulada(self.plataforma.currentText()),
                Cliente("C1", "Camila", "Av. Central 123"),
                (ItemPedido(Producto("Hamburguesa", 6500), 2),))

        def pagar(self):
            medios = [lambda: PagoTarjeta(), lambda: PagoTarjeta(False),
                      lambda: PagoBilletera(20000), lambda: PagoBilletera(1000)]
            resultado = self.servicio.pagar(self.pedido.id, medios[self.medio.currentIndex()]())
            if not resultado.aprobado:
                QMessageBox.information(self, "Pago", "Pago rechazado; puedes reintentar")

        def asignar(self):
            self.servicio.asignar(self.pedido.id, Repartidor("R1", "Diego", "Bicicleta"))

        def iniciar(self): self.servicio.iniciar_entrega(self.pedido.id)
        def entregar(self): self.servicio.entregar(self.pedido.id)

        def actualizar(self):
            estado = self.pedido.estado if self.pedido else None
            self.resumen.setText("Sin pedido" if not self.pedido else
                f"Total: ${self.pedido.total:,} CLP\n" + " → ".join(e.value for e in self.pedido.historial))
            for texto, requerido in [("Pagar", EstadoPedido.RECIBIDO), ("Asignar repartidor", EstadoPedido.PAGADO),
                    ("Iniciar entrega", EstadoPedido.ASIGNADO), ("Entregar", EstadoPedido.EN_CAMINO)]:
                self.botones[texto].setEnabled(estado is requerido)
            self.botones["Crear pedido"].setEnabled(estado in (None, EstadoPedido.ENTREGADO))

    app = QApplication(sys.argv)
    ventana = Ventana()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
