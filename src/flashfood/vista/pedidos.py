"""Creación de pedidos y carga de productos."""

import tkinter as tk
from tkinter import ttk

from flashfood.vista.comun import (
    Pantalla,
    configurar_combo,
    crear_tabla,
    informar,
    mostrar_error,
    pedir_confirmacion,
    pesos,
    titulo,
)


class Pedidos(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._clientes: dict[str, str] = {}
        self._productos: dict[str, str] = {}
        self._pedido_id: str | None = None
        titulo(self, "Pedidos")

        alta = ttk.LabelFrame(self, text="Nuevo pedido", padding=12)
        alta.pack(fill="x")
        self.cliente = tk.StringVar()
        ttk.Label(alta, text="Cliente").grid(row=0, column=0, sticky="w")
        self.combo_cliente = ttk.Combobox(alta, textvariable=self.cliente, state="readonly")
        self.combo_cliente.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(alta, text="Crear pedido", command=self.crear).grid(row=0, column=2, padx=(0, 8))
        self.boton_eliminar = ttk.Button(alta, text="Eliminar pedido", command=self.eliminar)
        self.boton_eliminar.grid(row=0, column=3)
        alta.columnconfigure(1, weight=1)

        marco, self.tabla = crear_tabla(
            self,
            ("id", "cliente", "estado", "total"),
            ("Pedido", "Cliente", "Estado", "Total"),
            (140, 200, 140, 120),
            altura=5,
        )
        marco.pack(fill="both", expand=True, pady=12)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

        edicion = ttk.LabelFrame(self, text="Productos del pedido seleccionado", padding=12)
        edicion.pack(fill="both", expand=True)
        self.producto = tk.StringVar()
        self.cantidad = tk.StringVar(value="1")
        ttk.Label(edicion, text="Producto").grid(row=0, column=0, sticky="w")
        self.combo_producto = ttk.Combobox(edicion, textvariable=self.producto, state="readonly")
        self.combo_producto.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Label(edicion, text="Cantidad").grid(row=0, column=2, sticky="w")
        ttk.Entry(edicion, textvariable=self.cantidad, width=8).grid(row=0, column=3, padx=(8, 0))
        self.boton_agregar = ttk.Button(edicion, text="Agregar", command=self.agregar)
        self.boton_quitar = ttk.Button(edicion, text="Quitar línea", command=self.quitar)
        self.boton_agregar.grid(row=0, column=4, padx=8)
        self.boton_quitar.grid(row=0, column=5)
        edicion.columnconfigure(1, weight=1)

        marco_lineas, self.lineas = crear_tabla(
            edicion,
            ("producto", "cantidad", "precio", "subtotal"),
            ("Producto", "Cantidad", "Precio", "Subtotal"),
            (220, 90, 110, 120),
            altura=4,
        )
        marco_lineas.grid(row=1, column=0, columnspan=6, sticky="nsew", pady=(12, 0))
        edicion.rowconfigure(1, weight=1)
        self.totales = ttk.Label(edicion, justify="left")
        self.totales.grid(row=2, column=0, columnspan=6, sticky="w", pady=(8, 0))

    def refrescar(self) -> None:
        self._clientes = {
            f"{cliente.nombre} — {cliente.direccion}": cliente.id for cliente in self.controlador.listar_clientes()
        }
        configurar_combo(self.combo_cliente, list(self._clientes), self.cliente.get())
        self._productos = {
            f"{producto.nombre} — {pesos(producto.precio)}": producto.id
            for producto in self.controlador.listar_productos()
        }
        configurar_combo(self.combo_producto, list(self._productos), self.producto.get())

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
                    pesos(pedido.total),
                ),
            )
        if seleccionado and self.tabla.exists(seleccionado):
            self.tabla.selection_set(seleccionado)
            self.tabla.see(seleccionado)
            self._mostrar(seleccionado)
        else:
            self._pedido_id = None
            self._mostrar(None)

    def crear(self) -> None:
        cliente_id = self._clientes.get(self.cliente.get(), "")
        ok, pedido = self.ejecutar(lambda: self.controlador.crear_pedido(cliente_id))
        if not ok:
            return
        self._pedido_id = pedido.id
        informar(self.winfo_toplevel(), "Pedido creado", "Ahora agrega los productos.")
        self.refrescar()

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        self._pedido_id = seleccion[0] if seleccion else None
        self._mostrar(self._pedido_id)

    def _mostrar(self, pedido_id: str | None) -> None:
        self.lineas.delete(*self.lineas.get_children())
        if not pedido_id:
            self.totales.configure(text="Selecciona o crea un pedido.")
            self._habilitar(False, False)
            return
        pedido = self.controlador.obtener_pedido(pedido_id)
        for detalle in pedido.detalles:
            self.lineas.insert(
                "",
                "end",
                iid=detalle.producto_id,
                values=(detalle.nombre, detalle.cantidad, pesos(detalle.precio_unitario), pesos(detalle.subtotal)),
            )
        condiciones = []
        if pedido.es_vip:
            condiciones.append("VIP")
        if pedido.hora_punta:
            condiciones.append("hora punta")
        if pedido.lluvia:
            condiciones.append("lluvia")
        texto_condiciones = ", ".join(condiciones) if condiciones else "sin recargos ni descuento"
        self.totales.configure(
            text=(
                f"Subtotal {pesos(pedido.subtotal)}    Descuento {pesos(pedido.descuento)}    "
                f"Despacho {pesos(pedido.costo_despacho)}    Total {pesos(pedido.total)}\n"
                f"Condiciones al crear el pedido: {texto_condiciones}."
            )
        )
        acciones = self.controlador.acciones(pedido_id)
        self._habilitar(acciones["puede_editar_items"], acciones["puede_cancelar"])

    def _habilitar(self, editar: bool, cancelar: bool) -> None:
        estado = "normal" if editar else "disabled"
        self.boton_agregar.configure(state=estado)
        self.boton_quitar.configure(state=estado)
        self.boton_eliminar.configure(state="normal" if cancelar else "disabled")

    def agregar(self) -> None:
        if not self._pedido_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un pedido.")
            return
        producto_id = self._productos.get(self.producto.get(), "")
        ok, _pedido = self.ejecutar(
            lambda: self.controlador.agregar_producto(self._pedido_id, producto_id, self.cantidad.get())
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Producto agregado", "La línea quedó en el pedido.")
        self.refrescar()

    def quitar(self) -> None:
        if not self._pedido_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un pedido.")
            return
        seleccion = self.lineas.selection()
        if not seleccion:
            mostrar_error(self.winfo_toplevel(), "Selecciona la línea que quieres quitar.")
            return
        ok, _pedido = self.ejecutar(lambda: self.controlador.quitar_producto(self._pedido_id, seleccion[0]))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Línea quitada", "El producto salió del pedido.")
        self.refrescar()

    def eliminar(self) -> None:
        if not self._pedido_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un pedido.")
            return
        if not pedir_confirmacion(
            self.winfo_toplevel(),
            "Eliminar pedido",
            "¿Eliminar este pedido? Si ya estaba pagado, el stock vuelve al inventario.",
        ):
            return
        pedido_id = self._pedido_id
        ok, _pedido = self.ejecutar(lambda: self.controlador.cancelar(pedido_id))
        if not ok:
            return
        self._pedido_id = None
        informar(self.winfo_toplevel(), "Pedido eliminado", "El pedido quedó cancelado.")
        self.refrescar()
