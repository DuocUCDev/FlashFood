"""Registro y consulta de clientes."""

import tkinter as tk
from tkinter import ttk

from flashfood.vista.comun import Pantalla, crear_tabla, informar, mostrar_error, pedir_confirmacion, titulo


class Clientes(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._cliente_id: str | None = None
        titulo(self, "Clientes")
        ttk.Label(self, text="Selecciona una fila para editar o eliminar ese cliente.").pack(anchor="w", pady=(0, 8))
        formulario = ttk.LabelFrame(self, text="Datos del cliente", padding=12)
        formulario.pack(fill="x")
        self.nombre = tk.StringVar()
        self.telefono = tk.StringVar()
        self.direccion = tk.StringVar()
        self.es_vip = tk.BooleanVar()
        for fila, texto, variable in (
            (0, "Nombre", self.nombre),
            (1, "Teléfono", self.telefono),
            (2, "Dirección", self.direccion),
        ):
            ttk.Label(formulario, text=texto).grid(row=fila, column=0, sticky="w", pady=4)
            ttk.Entry(formulario, textvariable=variable).grid(row=fila, column=1, sticky="ew", padx=(8, 0), pady=4)
        ttk.Checkbutton(formulario, text="Cliente VIP (10% sobre el subtotal)", variable=self.es_vip).grid(
            row=3, column=1, sticky="w", padx=(8, 0), pady=4
        )
        acciones = ttk.Frame(formulario)
        acciones.grid(row=4, column=1, sticky="e", pady=(8, 0))
        self.boton_registrar = ttk.Button(acciones, text="Registrar", command=self.registrar)
        self.boton_guardar = ttk.Button(acciones, text="Guardar cambios", command=self.guardar)
        self.boton_eliminar = ttk.Button(acciones, text="Eliminar", command=self.eliminar)
        self.boton_limpiar = ttk.Button(acciones, text="Limpiar", command=self.limpiar)
        for boton in (self.boton_registrar, self.boton_guardar, self.boton_eliminar, self.boton_limpiar):
            boton.pack(side="left", padx=(0, 8))
        formulario.columnconfigure(1, weight=1)

        marco, self.tabla = crear_tabla(
            self,
            ("nombre", "telefono", "direccion", "vip"),
            ("Nombre", "Teléfono", "Dirección", "VIP"),
            (180, 140, 280, 80),
        )
        marco.pack(fill="both", expand=True, pady=(12, 0))
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)
        self.limpiar()

    def refrescar(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        for cliente in self.controlador.listar_clientes():
            self.tabla.insert(
                "",
                "end",
                iid=cliente.id,
                values=(cliente.nombre, cliente.telefono, cliente.direccion, "Sí" if cliente.es_vip else "No"),
            )

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        cliente = self.controlador.obtener_cliente(seleccion[0])
        self._cliente_id = cliente.id
        self.nombre.set(cliente.nombre)
        self.telefono.set(cliente.telefono)
        self.direccion.set(cliente.direccion)
        self.es_vip.set(cliente.es_vip)
        self.boton_registrar.configure(state="disabled")
        self.boton_guardar.configure(state="normal")
        self.boton_eliminar.configure(state="normal")

    def limpiar(self) -> None:
        self._cliente_id = None
        self.nombre.set("")
        self.telefono.set("")
        self.direccion.set("")
        self.es_vip.set(False)
        self.boton_registrar.configure(state="normal")
        self.boton_guardar.configure(state="disabled")
        self.boton_eliminar.configure(state="disabled")
        if self.tabla.selection():
            self.tabla.selection_remove(self.tabla.selection())

    def registrar(self) -> None:
        ok, _cliente = self.ejecutar(
            lambda: self.controlador.registrar_cliente(
                self.nombre.get(),
                self.telefono.get(),
                self.direccion.get(),
                bool(self.es_vip.get()),
            )
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Cliente registrado", "El cliente ya puede hacer pedidos.")
        self.limpiar()
        self.refrescar()

    def guardar(self) -> None:
        if not self._cliente_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un cliente de la tabla para editarlo.")
            return
        ok, _cliente = self.ejecutar(
            lambda: self.controlador.editar_cliente(
                self._cliente_id,
                self.nombre.get(),
                self.telefono.get(),
                self.direccion.get(),
                bool(self.es_vip.get()),
            )
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Cliente actualizado", "Los cambios quedaron guardados.")
        self.limpiar()
        self.refrescar()

    def eliminar(self) -> None:
        if not self._cliente_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un cliente de la tabla para eliminarlo.")
            return
        if not pedir_confirmacion(self.winfo_toplevel(), "Eliminar cliente", "¿Eliminar el cliente seleccionado?"):
            return
        ok, _resultado = self.ejecutar(lambda: self.controlador.eliminar_cliente(self._cliente_id))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Cliente eliminado", "El cliente salió del registro.")
        self.limpiar()
        self.refrescar()
