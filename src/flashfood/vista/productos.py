"""Alta, edición, eliminación y consulta de comidas y bebidas."""

import tkinter as tk
from tkinter import ttk

from flashfood.vista.comun import Pantalla, crear_tabla, informar, mostrar_error, pedir_confirmacion, pesos, titulo


class Productos(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._producto_id: str | None = None
        titulo(self, "Productos")
        ttk.Label(self, text="Selecciona una fila para editar o eliminar ese producto.").pack(anchor="w", pady=(0, 8))

        formulario = ttk.LabelFrame(self, text="Datos del producto", padding=12)
        formulario.pack(fill="x")
        self.tipo = tk.StringVar(value="Comida")
        self.nombre = tk.StringVar()
        self.precio = tk.StringVar()
        self.stock = tk.StringVar(value="0")
        self.extra = tk.StringVar()

        ttk.Label(formulario, text="Tipo").grid(row=0, column=0, sticky="w", pady=4)
        self.tipo_combo = ttk.Combobox(formulario, textvariable=self.tipo, values=("Comida", "Bebida"), state="readonly")
        self.tipo_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        self.tipo_combo.bind("<<ComboboxSelected>>", lambda _evento: self._actualizar_extra())

        self._campo(formulario, 1, "Nombre", self.nombre)
        self._campo(formulario, 2, "Precio (CLP)", self.precio)
        self._campo(formulario, 3, "Stock", self.stock)
        self.lbl_extra = ttk.Label(formulario, text="Categoría")
        self.lbl_extra.grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=self.extra).grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=4)
        formulario.columnconfigure(1, weight=1)

        acciones = ttk.Frame(formulario)
        acciones.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))
        self.boton_registrar = ttk.Button(acciones, text="Registrar", command=self.registrar)
        self.boton_guardar = ttk.Button(acciones, text="Guardar cambios", command=self.guardar)
        self.boton_eliminar = ttk.Button(acciones, text="Eliminar", command=self.eliminar)
        self.boton_limpiar = ttk.Button(acciones, text="Limpiar", command=self.limpiar)
        for boton in (self.boton_registrar, self.boton_guardar, self.boton_eliminar, self.boton_limpiar):
            boton.pack(side="left", padx=(0, 8))

        ttk.Label(
            self,
            text="Disponible es el stock que aún se puede agregar a pedidos creados.",
        ).pack(anchor="w", pady=(12, 4))
        marco, self.tabla = crear_tabla(
            self,
            ("tipo", "nombre", "precio", "stock", "disponible", "detalle"),
            ("Tipo", "Nombre", "Precio", "Stock", "Disponible", "Detalle"),
            (100, 220, 110, 80, 100, 160),
        )
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)
        self.limpiar()

    def _campo(self, formulario, fila: int, texto: str, variable: tk.StringVar) -> None:
        ttk.Label(formulario, text=texto).grid(row=fila, column=0, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=variable).grid(row=fila, column=1, sticky="ew", padx=(8, 0), pady=4)

    def _actualizar_extra(self) -> None:
        self.lbl_extra.configure(text="Mililitros" if self.tipo.get() == "Bebida" else "Categoría")

    def refrescar(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        for producto in self.controlador.listar_productos():
            self.tabla.insert(
                "",
                "end",
                iid=producto.id,
                values=(
                    producto.tipo_visible,
                    producto.nombre,
                    pesos(producto.precio),
                    producto.stock,
                    self.controlador.stock_disponible(producto.id),
                    producto.detalle,
                ),
            )

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        producto = self.controlador.obtener_producto(seleccion[0])
        self._producto_id = producto.id
        self.nombre.set(producto.nombre)
        self.precio.set(str(producto.precio))
        self.stock.set(str(producto.stock))
        self.tipo.set(producto.tipo_visible)
        self.extra.set(str(producto.mililitros) if producto.tipo == "bebida" else producto.categoria)
        self.tipo_combo.configure(state="disabled")
        self._actualizar_extra()
        self.boton_registrar.configure(state="disabled")
        self.boton_guardar.configure(state="normal")
        self.boton_eliminar.configure(state="normal")

    def limpiar(self) -> None:
        self._producto_id = None
        self.nombre.set("")
        self.precio.set("")
        self.stock.set("0")
        self.extra.set("")
        self.tipo.set("Comida")
        self.tipo_combo.configure(state="readonly")
        self._actualizar_extra()
        self.boton_registrar.configure(state="normal")
        self.boton_guardar.configure(state="disabled")
        self.boton_eliminar.configure(state="disabled")
        if self.tabla.selection():
            self.tabla.selection_remove(self.tabla.selection())

    def registrar(self) -> None:
        ok, _producto = self.ejecutar(
            lambda: self.controlador.registrar_producto(
                self.tipo.get(), self.nombre.get(), self.precio.get(), self.stock.get(), self.extra.get()
            )
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Producto registrado", "El producto quedó en el catálogo.")
        self.limpiar()
        self.refrescar()

    def guardar(self) -> None:
        if not self._producto_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un producto de la tabla para editarlo.")
            return
        ok, _producto = self.ejecutar(
            lambda: self.controlador.editar_producto(
                self._producto_id, self.nombre.get(), self.precio.get(), self.stock.get(), self.extra.get()
            )
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Producto actualizado", "Los cambios quedaron guardados.")
        self.limpiar()
        self.refrescar()

    def eliminar(self) -> None:
        if not self._producto_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un producto de la tabla para eliminarlo.")
            return
        if not pedir_confirmacion(self.winfo_toplevel(), "Eliminar producto", "¿Eliminar el producto seleccionado?"):
            return
        ok, _resultado = self.ejecutar(lambda: self.controlador.eliminar_producto(self._producto_id))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Producto eliminado", "El producto salió del catálogo.")
        self.limpiar()
        self.refrescar()
