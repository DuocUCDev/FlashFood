"""Piezas compartidas por las pantallas."""

import tkinter as tk
from tkinter import messagebox, ttk

from flashfood.modelo.errores import PersistenciaError, ReglaNegocioError
from flashfood.modelo.formato import pesos

MODULOS = (
    ("inicio", "Inicio"),
    ("productos", "Productos"),
    ("clientes", "Clientes"),
    ("pedidos", "Pedidos"),
    ("detalle", "Detalle del pedido"),
    ("pagos", "Pagos"),
    ("repartidores", "Repartidores"),
    ("seguimiento", "Seguimiento"),
)


def informar(parent: tk.Misc, titulo: str, mensaje: str) -> None:
    messagebox.showinfo(titulo, mensaje, parent=parent)


def mostrar_error(parent: tk.Misc, mensaje: str) -> None:
    messagebox.showerror("No se pudo completar", mensaje, parent=parent)


def pedir_confirmacion(parent: tk.Misc, titulo: str, mensaje: str) -> bool:
    return bool(messagebox.askyesno(titulo, mensaje, parent=parent))


def titulo(parent: tk.Misc, texto: str) -> ttk.Label:
    etiqueta = ttk.Label(parent, text=texto, style="Titulo.TLabel")
    etiqueta.pack(anchor="w", pady=(0, 12))
    return etiqueta


def crear_tabla(
    parent: tk.Misc,
    columnas: tuple[str, ...],
    encabezados: tuple[str, ...],
    anchos: tuple[int, ...],
    altura: int = 8,
) -> tuple[ttk.Frame, ttk.Treeview]:
    marco = ttk.Frame(parent)
    tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=altura, selectmode="browse")
    scroll = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    for columna, encabezado, ancho in zip(columnas, encabezados, anchos):
        tabla.heading(columna, text=encabezado)
        anchor = "e" if columna in {"precio", "stock", "disponible", "cantidad", "subtotal", "total"} else "w"
        tabla.column(columna, width=ancho, anchor=anchor)
    tabla.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")
    marco.rowconfigure(0, weight=1)
    marco.columnconfigure(0, weight=1)
    return marco, tabla


def configurar_combo(combo: ttk.Combobox, etiquetas: list[str], actual: str) -> None:
    combo["values"] = etiquetas
    if actual in etiquetas:
        combo.set(actual)
    elif etiquetas:
        combo.current(0)
    else:
        combo.set("")


class Pantalla(ttk.Frame):
    """Las pantallas llaman al controlador. Las reglas viven en el modelo."""

    def __init__(self, master: tk.Misc, controlador):
        super().__init__(master, padding=16)
        self.controlador = controlador

    def refrescar(self) -> None:
        return None

    def ejecutar(self, accion):
        try:
            return True, accion()
        except (ReglaNegocioError, PersistenciaError) as error:
            mostrar_error(self.winfo_toplevel(), str(error))
            return False, None


__all__ = [
    "MODULOS",
    "Pantalla",
    "configurar_combo",
    "crear_tabla",
    "informar",
    "mostrar_error",
    "pedir_confirmacion",
    "pesos",
    "titulo",
]
