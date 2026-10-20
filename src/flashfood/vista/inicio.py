"""Pantalla de inicio: acceso a módulos y condiciones de la operación."""

import tkinter as tk
from tkinter import ttk

from flashfood.vista.comun import MODULOS, Pantalla, titulo


class Inicio(Pantalla):
    def __init__(self, master, controlador, navegar):
        super().__init__(master, controlador)
        self._navegar = navegar
        self._sincronizando = False
        titulo(self, "Operación 13:00")
        ttk.Label(
            self,
            text="FlashFood recibe pedidos, cobra, prepara y asigna un repartidor para la entrega.",
            wraplength=760,
        ).pack(anchor="w")
        self.reglas = ttk.Label(self, wraplength=760)
        self.reglas.pack(anchor="w", pady=(8, 12))

        condiciones = ttk.LabelFrame(self, text="Condiciones del despacho", padding=12)
        condiciones.pack(fill="x", pady=(0, 12))
        self.hora_punta = tk.BooleanVar()
        self.lluvia = tk.BooleanVar()
        ttk.Checkbutton(
            condiciones,
            text="Hora punta (+25% al despacho)",
            variable=self.hora_punta,
            command=self.aplicar_condiciones,
        ).pack(anchor="w")
        ttk.Checkbutton(
            condiciones,
            text="Lluvia (+$1.000 al despacho)",
            variable=self.lluvia,
            command=self.aplicar_condiciones,
        ).pack(anchor="w", pady=(6, 0))

        self.resumen = ttk.Label(self, justify="left")
        self.resumen.pack(anchor="w", pady=(0, 12))

        acceso = ttk.LabelFrame(self, text="Módulos", padding=12)
        acceso.pack(fill="x")
        visibles = [(clave, etiqueta) for clave, etiqueta in MODULOS if clave != "inicio"]
        for indice, (clave, etiqueta) in enumerate(visibles):
            boton = ttk.Button(acceso, text=etiqueta, command=lambda destino=clave: self._navegar(destino))
            boton.grid(row=indice // 3, column=indice % 3, sticky="ew", padx=4, pady=4)
        for columna in range(3):
            acceso.columnconfigure(columna, weight=1)

    def refrescar(self) -> None:
        self.reglas.configure(text=self.controlador.reglas())
        self._sincronizando = True
        self.hora_punta.set(self.controlador.hora_punta)
        self.lluvia.set(self.controlador.lluvia)
        self._sincronizando = False
        datos = self.controlador.resumen()
        lineas = [
            f"Productos: {datos['productos']}",
            f"Clientes: {datos['clientes']}",
            f"Repartidores disponibles: {datos['disponibles']} de {datos['repartidores']}",
            "Pedidos: " + ", ".join(f"{estado} {cantidad}" for estado, cantidad in datos["pedidos"].items()),
        ]
        self.resumen.configure(text="\n".join(lineas))

    def aplicar_condiciones(self) -> None:
        if self._sincronizando:
            return
        self.ejecutar(
            lambda: self.controlador.definir_condiciones(bool(self.hora_punta.get()), bool(self.lluvia.get()))
        )
        self.refrescar()
