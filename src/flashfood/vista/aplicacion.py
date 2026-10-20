"""Ventana principal y menú de navegación."""

import tkinter as tk
from tkinter import ttk

from flashfood.controladores.controlador import Controlador
from flashfood.vista.clientes import Clientes
from flashfood.vista.comun import MODULOS, informar
from flashfood.vista.detalle import Detalle
from flashfood.vista.inicio import Inicio
from flashfood.vista.pagos import Pagos
from flashfood.vista.pedidos import Pedidos
from flashfood.vista.productos import Productos
from flashfood.vista.repartidores import Repartidores
from flashfood.vista.seguimiento import Seguimiento


class Aplicacion(tk.Tk):
    def __init__(self, controlador: Controlador):
        super().__init__()
        self.controlador = controlador
        self.title("FlashFood — Operación 13:00")
        self.geometry("1180x720")
        self.minsize(980, 600)
        self._aplicar_estilo()
        self._crear_menu()
        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True)
        self._navegacion = ttk.Frame(cuerpo, padding=(12, 16, 8, 16))
        self._navegacion.pack(side="left", fill="y")
        ttk.Label(self._navegacion, text="Módulos", style="Titulo.TLabel").pack(anchor="w", pady=(0, 12))
        self._contenido = ttk.Frame(cuerpo)
        self._contenido.pack(side="left", fill="both", expand=True)
        self._botones_nav = {}
        for clave, etiqueta in MODULOS:
            boton = ttk.Button(
                self._navegacion,
                text=etiqueta,
                style="Nav.TButton",
                command=lambda destino=clave: self.mostrar(destino),
            )
            boton.pack(fill="x", pady=3)
            self._botones_nav[clave] = boton
        self._pantallas = {
            "inicio": Inicio(self._contenido, controlador, self.mostrar),
            "productos": Productos(self._contenido, controlador),
            "clientes": Clientes(self._contenido, controlador),
            "pedidos": Pedidos(self._contenido, controlador),
            "detalle": Detalle(self._contenido, controlador),
            "pagos": Pagos(self._contenido, controlador),
            "repartidores": Repartidores(self._contenido, controlador),
            "seguimiento": Seguimiento(self._contenido, controlador),
        }
        self._actual = None
        self.mostrar("inicio")

    def _aplicar_estilo(self) -> None:
        self.configure(background="#f4f1ea")
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure(".", background="#f4f1ea")
        estilo.configure("TFrame", background="#f4f1ea")
        estilo.configure("TLabel", background="#f4f1ea")
        estilo.configure("TLabelframe", background="#f4f1ea")
        estilo.configure("TLabelframe.Label", background="#f4f1ea")
        estilo.configure("TCheckbutton", background="#f4f1ea")
        estilo.configure("Titulo.TLabel", font=("Helvetica", 20, "bold"), background="#f4f1ea")
        estilo.configure("TButton", padding=6)
        estilo.configure("Nav.TButton", padding=(12, 8), anchor="w")
        estilo.configure("NavActivo.TButton", padding=(12, 8), anchor="w", background="#e4d3b4")
        estilo.configure("Treeview", rowheight=26)
        estilo.configure("Treeview.Heading", font=("Helvetica", 11, "bold"))

    def _crear_menu(self) -> None:
        barra = tk.Menu(self)
        archivo = tk.Menu(barra, tearoff=0)
        archivo.add_command(label="Salir", command=self.destroy)
        barra.add_cascade(label="Archivo", menu=archivo)
        modulos = tk.Menu(barra, tearoff=0)
        for clave, etiqueta in MODULOS:
            modulos.add_command(label=etiqueta, command=lambda destino=clave: self.mostrar(destino))
        barra.add_cascade(label="Módulos", menu=modulos)
        self.configure(menu=barra)

    def mostrar(self, nombre: str) -> None:
        if self._actual is not None:
            self._actual.pack_forget()
        pantalla = self._pantallas[nombre]
        pantalla.refrescar()
        pantalla.pack(fill="both", expand=True)
        self._actual = pantalla
        for clave, boton in self._botones_nav.items():
            boton.configure(style="NavActivo.TButton" if clave == nombre else "Nav.TButton")


def iniciar(directorio=None) -> None:
    controlador = Controlador(directorio)
    aplicacion = Aplicacion(controlador)
    if controlador.advertencia:
        aplicacion.after(200, lambda: informar(aplicacion, "Datos", controlador.advertencia))
    aplicacion.mainloop()
