"""Consulta del detalle, los totales y el historial de un pedido."""

import tkinter as tk
from tkinter import ttk

from flashfood.vista.comun import Pantalla, configurar_combo, crear_tabla, pesos, titulo


class Detalle(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._pedidos: dict[str, str] = {}
        titulo(self, "Detalle del pedido")
        self.pedido = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.pedido, state="readonly")
        self.combo.pack(fill="x")
        self.combo.bind("<<ComboboxSelected>>", lambda _evento: self.mostrar())

        marco, self.tabla = crear_tabla(
            self,
            ("producto", "cantidad", "precio", "subtotal"),
            ("Producto", "Cantidad", "Precio", "Subtotal"),
            (240, 100, 120, 140),
        )
        marco.pack(fill="both", expand=True, pady=12)
        self.resumen = ttk.Label(self, justify="left")
        self.resumen.pack(anchor="w")

    def refrescar(self) -> None:
        actual = self.pedido.get()
        self._pedidos = {}
        etiquetas = []
        for pedido in self.controlador.listar_pedidos():
            etiqueta = f"{pedido.id} — {self.controlador.nombre_cliente(pedido.cliente_id)} — {pedido.estado.etiqueta}"
            self._pedidos[etiqueta] = pedido.id
            etiquetas.append(etiqueta)
        configurar_combo(self.combo, etiquetas, actual)
        self.mostrar()

    def mostrar(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        pedido_id = self._pedidos.get(self.pedido.get())
        if not pedido_id:
            self.resumen.configure(text="No hay pedidos para consultar.")
            return
        pedido = self.controlador.obtener_pedido(pedido_id)
        for detalle in pedido.detalles:
            self.tabla.insert(
                "",
                "end",
                values=(detalle.nombre, detalle.cantidad, pesos(detalle.precio_unitario), pesos(detalle.subtotal)),
            )
        pago = "Sin pago" if pedido.pago is None else f"{pedido.pago.medio} · {pedido.pago.referencia}"
        self.resumen.configure(
            text=(
                f"Cliente: {self.controlador.nombre_cliente(pedido.cliente_id)}\n"
                f"Subtotal: {pesos(pedido.subtotal)}\n"
                f"Descuento VIP: {pesos(pedido.descuento)}\n"
                f"Despacho: {pesos(pedido.costo_despacho)}\n"
                f"Total: {pesos(pedido.total)}\n"
                f"Pago: {pago}\n"
                f"Repartidor: {self.controlador.nombre_repartidor(pedido.repartidor_id)}\n"
                f"Historial: {pedido.historial_texto()}"
            )
        )
