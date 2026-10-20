"""Registro, consulta y asignación de repartidores disponibles."""

import tkinter as tk
from tkinter import ttk

from flashfood.vista.comun import (
    Pantalla,
    configurar_combo,
    crear_tabla,
    informar,
    mostrar_error,
    pedir_confirmacion,
    titulo,
)


class Repartidores(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._pedidos: dict[str, str] = {}
        self._repartidores: dict[str, str] = {}
        self._repartidor_id: str | None = None
        titulo(self, "Repartidores")
        ttk.Label(
            self,
            text="Un repartidor se asigna cuando el pedido está en preparación y no puede llevar dos entregas a la vez.",
            wraplength=760,
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(self, text="Selecciona una fila para editar o eliminar ese repartidor.").pack(anchor="w", pady=(0, 8))
        formulario = ttk.LabelFrame(self, text="Datos del repartidor", padding=12)
        formulario.pack(fill="x")
        self.nombre = tk.StringVar()
        self.vehiculo = tk.StringVar()
        ttk.Label(formulario, text="Nombre").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=self.nombre).grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(formulario, text="Vehículo").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=self.vehiculo).grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        acciones = ttk.Frame(formulario)
        acciones.grid(row=2, column=1, sticky="e", pady=(8, 0))
        self.boton_registrar = ttk.Button(acciones, text="Registrar", command=self.registrar)
        self.boton_guardar = ttk.Button(acciones, text="Guardar cambios", command=self.guardar)
        self.boton_eliminar = ttk.Button(acciones, text="Eliminar", command=self.eliminar)
        self.boton_limpiar = ttk.Button(acciones, text="Limpiar", command=self.limpiar)
        for boton in (self.boton_registrar, self.boton_guardar, self.boton_eliminar, self.boton_limpiar):
            boton.pack(side="left", padx=(0, 8))
        formulario.columnconfigure(1, weight=1)

        marco, self.tabla = crear_tabla(
            self,
            ("nombre", "vehiculo", "estado"),
            ("Nombre", "Vehículo", "Estado"),
            (200, 160, 140),
            altura=5,
        )
        marco.pack(fill="both", expand=True, pady=12)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)
        self.limpiar()

        asignacion = ttk.LabelFrame(self, text="Asignar entrega", padding=12)
        asignacion.pack(fill="x")
        self.pedido = tk.StringVar()
        self.repartidor = tk.StringVar()
        ttk.Label(asignacion, text="Pedido en preparación").grid(row=0, column=0, sticky="w", pady=4)
        self.combo_pedido = ttk.Combobox(asignacion, textvariable=self.pedido, state="readonly")
        self.combo_pedido.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(asignacion, text="Repartidor disponible").grid(row=1, column=0, sticky="w", pady=4)
        self.combo_repartidor = ttk.Combobox(asignacion, textvariable=self.repartidor, state="readonly")
        self.combo_repartidor.grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(asignacion, text="Asignar", command=self.asignar).grid(row=2, column=1, sticky="e", pady=(8, 0))
        asignacion.columnconfigure(1, weight=1)

    def refrescar(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        for repartidor in self.controlador.listar_repartidores():
            self.tabla.insert(
                "",
                "end",
                iid=repartidor.id,
                values=(repartidor.nombre, repartidor.vehiculo, "Disponible" if repartidor.disponible else "En entrega"),
            )
        self._pedidos = {}
        etiquetas_pedidos = []
        for pedido in self.controlador.listar_pedidos():
            if not self.controlador.acciones(pedido.id)["puede_asignar"]:
                continue
            etiqueta = f"{pedido.id} — {self.controlador.nombre_cliente(pedido.cliente_id)}"
            self._pedidos[etiqueta] = pedido.id
            etiquetas_pedidos.append(etiqueta)
        configurar_combo(self.combo_pedido, etiquetas_pedidos, self.pedido.get())

        self._repartidores = {
            f"{item.nombre} — {item.vehiculo}": item.id
            for item in self.controlador.listar_repartidores()
            if item.disponible
        }
        configurar_combo(self.combo_repartidor, list(self._repartidores), self.repartidor.get())

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        repartidor = self.controlador.obtener_repartidor(seleccion[0])
        self._repartidor_id = repartidor.id
        self.nombre.set(repartidor.nombre)
        self.vehiculo.set(repartidor.vehiculo)
        self.boton_registrar.configure(state="disabled")
        self.boton_guardar.configure(state="normal")
        self.boton_eliminar.configure(state="normal")

    def limpiar(self) -> None:
        self._repartidor_id = None
        self.nombre.set("")
        self.vehiculo.set("")
        self.boton_registrar.configure(state="normal")
        self.boton_guardar.configure(state="disabled")
        self.boton_eliminar.configure(state="disabled")
        if self.tabla.selection():
            self.tabla.selection_remove(self.tabla.selection())

    def registrar(self) -> None:
        ok, _repartidor = self.ejecutar(
            lambda: self.controlador.registrar_repartidor(self.nombre.get(), self.vehiculo.get())
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Repartidor registrado", "Ya puede recibir una entrega.")
        self.limpiar()
        self.refrescar()

    def guardar(self) -> None:
        if not self._repartidor_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un repartidor de la tabla para editarlo.")
            return
        ok, _repartidor = self.ejecutar(
            lambda: self.controlador.editar_repartidor(self._repartidor_id, self.nombre.get(), self.vehiculo.get())
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Repartidor actualizado", "Los cambios quedaron guardados.")
        self.limpiar()
        self.refrescar()

    def eliminar(self) -> None:
        if not self._repartidor_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un repartidor de la tabla para eliminarlo.")
            return
        if not pedir_confirmacion(
            self.winfo_toplevel(), "Eliminar repartidor", "¿Eliminar el repartidor seleccionado?"
        ):
            return
        ok, _resultado = self.ejecutar(lambda: self.controlador.eliminar_repartidor(self._repartidor_id))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Repartidor eliminado", "El repartidor salió del registro.")
        self.limpiar()
        self.refrescar()

    def asignar(self) -> None:
        pedido_id = self._pedidos.get(self.pedido.get(), "")
        repartidor_id = self._repartidores.get(self.repartidor.get(), "")
        if not pedido_id or not repartidor_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un pedido en preparación y un repartidor disponible.")
            return
        ok, _pedido = self.ejecutar(lambda: self.controlador.asignar_repartidor(pedido_id, repartidor_id))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Repartidor asignado", "El pedido ya puede despacharse.")
        self.refrescar()
