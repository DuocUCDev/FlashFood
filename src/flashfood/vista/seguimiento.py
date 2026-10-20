"""Consulta y avance del estado de los pedidos."""

import tkinter as tk
from tkinter import ttk

from flashfood.vista.comun import Pantalla, crear_tabla, informar, mostrar_error, pedir_confirmacion, pesos, titulo


class Seguimiento(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._pedido_id: str | None = None
        titulo(self, "Seguimiento")
        ttk.Label(
            self,
            text="Creado → Pagado → En preparación → En camino → Entregado. Cancelar solo antes del despacho.",
            wraplength=760,
        ).pack(anchor="w", pady=(0, 8))

        marco, self.tabla = crear_tabla(
            self,
            ("id", "cliente", "estado", "repartidor", "total"),
            ("Pedido", "Cliente", "Estado", "Repartidor", "Total"),
            (140, 180, 140, 160, 110),
        )
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

        self.historial = ttk.Label(self, wraplength=760)
        self.historial.pack(anchor="w", pady=8)
        acciones = ttk.Frame(self)
        acciones.pack(fill="x")
        self.botones = {
            "preparar": ttk.Button(acciones, text="Iniciar preparación", command=self.preparar),
            "despachar": ttk.Button(acciones, text="Despachar", command=self.despachar),
            "entregar": ttk.Button(acciones, text="Marcar entregado", command=self.entregar),
            "cancelar": ttk.Button(acciones, text="Cancelar pedido", command=self.cancelar),
        }
        for boton in self.botones.values():
            boton.pack(side="left", padx=(0, 8))
        self._aplicar(None)

    def refrescar(self) -> None:
        seleccionado = self._pedido_id
        self.tabla.delete(*self.tabla.get_children())
        for pedido in self.controlador.listar_pedidos():
            self.tabla.insert(
                "",
                "end",
                iid=pedido.id,
                values=(
                    pedido.id,
                    self.controlador.nombre_cliente(pedido.cliente_id),
                    pedido.estado.etiqueta,
                    self.controlador.nombre_repartidor(pedido.repartidor_id),
                    pesos(pedido.total),
                ),
            )
        if seleccionado and self.tabla.exists(seleccionado):
            self.tabla.selection_set(seleccionado)
            self.al_seleccionar()
        else:
            self._pedido_id = None
            self.historial.configure(text="Selecciona un pedido.")
            self._aplicar(None)

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            self._pedido_id = None
            self.historial.configure(text="Selecciona un pedido.")
            self._aplicar(None)
            return
        self._pedido_id = seleccion[0]
        pedido = self.controlador.obtener_pedido(self._pedido_id)
        self.historial.configure(text=pedido.historial_texto())
        self._aplicar(self.controlador.acciones(self._pedido_id))

    def _aplicar(self, acciones: dict | None) -> None:
        habilitado = {
            "preparar": False,
            "despachar": False,
            "entregar": False,
            "cancelar": False,
        }
        if acciones:
            habilitado = {
                "preparar": acciones["puede_preparar"],
                "despachar": acciones["puede_despachar"],
                "entregar": acciones["puede_entregar"],
                "cancelar": acciones["puede_cancelar"],
            }
        for clave, boton in self.botones.items():
            boton.configure(state="normal" if habilitado[clave] else "disabled")

    def preparar(self) -> None:
        self._operar(lambda: self.controlador.preparar(self._pedido_id or ""), "El pedido está en preparación.")

    def despachar(self) -> None:
        self._operar(lambda: self.controlador.despachar(self._pedido_id or ""), "El pedido va en camino.")

    def entregar(self) -> None:
        self._operar(lambda: self.controlador.entregar(self._pedido_id or ""), "El pedido fue entregado.")

    def cancelar(self) -> None:
        if not self._pedido_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un pedido.")
            return
        if not pedir_confirmacion(self.winfo_toplevel(), "Cancelar pedido", "¿Cancelar el pedido seleccionado?"):
            return
        self._operar(lambda: self.controlador.cancelar(self._pedido_id), "El pedido fue cancelado.")

    def _operar(self, accion, mensaje: str) -> None:
        if not self._pedido_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un pedido.")
            return
        ok, _pedido = self.ejecutar(accion)
        if not ok:
            return
        informar(self.winfo_toplevel(), "Seguimiento", mensaje)
        self.refrescar()
