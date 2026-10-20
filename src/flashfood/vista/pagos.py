"""Selección del medio de pago y simulación de la transacción."""

import tkinter as tk
from tkinter import ttk

from flashfood.vista.comun import Pantalla, configurar_combo, informar, mostrar_error, pesos, titulo


class Pagos(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._pedidos: dict[str, str] = {}
        titulo(self, "Pagos")
        ttk.Label(
            self,
            text="Un pago rechazado no confirma el pedido ni descuenta stock. Un pedido pagado no se vuelve a cobrar.",
            wraplength=760,
        ).pack(anchor="w", pady=(0, 8))

        self.pedido = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.pedido, state="readonly")
        self.combo.pack(fill="x")
        self.combo.bind("<<ComboboxSelected>>", lambda _evento: self.mostrar_total())
        self.total = ttk.Label(self, font=("Helvetica", 14, "bold"))
        self.total.pack(anchor="w", pady=8)

        self.medio = tk.StringVar(value="Tarjeta")
        self.combo_medio = ttk.Combobox(
            self,
            textvariable=self.medio,
            values=("Tarjeta", "Efectivo", "Billetera digital", "Transferencia"),
            state="readonly",
        )
        self.combo_medio.pack(fill="x")
        self.combo_medio.bind("<<ComboboxSelected>>", lambda _evento: self.mostrar_campos())

        self.rechazar_tarjeta = tk.BooleanVar()
        self.monto = tk.StringVar()
        self.saldo = tk.StringVar()
        self.operacion = tk.StringVar()
        self.rechazar_transferencia = tk.BooleanVar()
        self.marco_tarjeta = self._marco_check("Simular rechazo de la tarjeta", self.rechazar_tarjeta)
        self.marco_efectivo = self._marco_entrada("Monto recibido", self.monto)
        self.marco_billetera = self._marco_entrada("Saldo de la billetera", self.saldo)
        self.marco_transferencia = ttk.Frame(self)
        ttk.Label(self.marco_transferencia, text="Número de operación").pack(anchor="w")
        ttk.Entry(self.marco_transferencia, textvariable=self.operacion).pack(fill="x", pady=(4, 8))
        ttk.Checkbutton(
            self.marco_transferencia,
            text="Simular rechazo de la transferencia",
            variable=self.rechazar_transferencia,
        ).pack(anchor="w")

        ttk.Button(self, text="Procesar pago", command=self.procesar).pack(anchor="e", pady=(12, 0))
        self.mostrar_campos()

    def _marco_check(self, texto: str, variable: tk.BooleanVar) -> ttk.Frame:
        marco = ttk.Frame(self)
        ttk.Checkbutton(marco, text=texto, variable=variable).pack(anchor="w")
        return marco

    def _marco_entrada(self, texto: str, variable: tk.StringVar) -> ttk.Frame:
        marco = ttk.Frame(self)
        ttk.Label(marco, text=texto).pack(anchor="w")
        ttk.Entry(marco, textvariable=variable).pack(fill="x", pady=(4, 0))
        return marco

    def refrescar(self) -> None:
        actual = self.pedido.get()
        self._pedidos = {}
        etiquetas = []
        for pedido in self.controlador.listar_pedidos():
            if not self.controlador.acciones(pedido.id)["puede_pagar"]:
                continue
            etiqueta = f"{pedido.id} — {self.controlador.nombre_cliente(pedido.cliente_id)} — {pesos(pedido.total)}"
            self._pedidos[etiqueta] = pedido.id
            etiquetas.append(etiqueta)
        configurar_combo(self.combo, etiquetas, actual)
        self.mostrar_total()

    def mostrar_total(self) -> None:
        pedido_id = self._pedidos.get(self.pedido.get())
        if not pedido_id:
            self.total.configure(text="No hay pedidos pendientes de pago.")
            return
        pedido = self.controlador.obtener_pedido(pedido_id)
        self.total.configure(text=f"Total a cobrar: {pesos(pedido.total)}")

    def mostrar_campos(self) -> None:
        for marco in (self.marco_tarjeta, self.marco_efectivo, self.marco_billetera, self.marco_transferencia):
            marco.pack_forget()
        elegido = {
            "Tarjeta": self.marco_tarjeta,
            "Efectivo": self.marco_efectivo,
            "Billetera digital": self.marco_billetera,
            "Transferencia": self.marco_transferencia,
        }.get(self.medio.get(), self.marco_tarjeta)
        elegido.pack(fill="x", pady=(12, 0))

    def procesar(self) -> None:
        pedido_id = self._pedidos.get(self.pedido.get(), "")
        if not pedido_id:
            mostrar_error(self.winfo_toplevel(), "Selecciona un pedido creado que tenga productos.")
            return
        medio = self.medio.get()
        rechazar = self.rechazar_tarjeta.get() if medio == "Tarjeta" else self.rechazar_transferencia.get()
        ok, resultado = self.ejecutar(
            lambda: self.controlador.pagar(
                pedido_id,
                medio,
                rechazar if medio in {"Tarjeta", "Transferencia"} else False,
                self.monto.get(),
                self.saldo.get(),
                self.operacion.get(),
            )
        )
        if not ok:
            return
        titulo_aviso = "Pago aprobado" if resultado.aprobado else "Pago rechazado"
        informar(self.winfo_toplevel(), titulo_aviso, resultado.mensaje)
        self.refrescar()
