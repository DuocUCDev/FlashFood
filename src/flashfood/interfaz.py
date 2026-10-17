import tkinter as tk
from tkinter import ttk, messagebox

class VentanaFlashFood:

    def __init__(self, raiz):
        self.raiz = raiz

        self.raiz.title("FlashFood - Productos")
        self.raiz.geometry("750x450")
        self.raiz.minsize(600, 350)

        self.nombre = tk.StringVar()
        self.precio = tk.StringVar()
        self.stock = tk.StringVar(value="0")

        self.crear_componentes()

    def crear_componentes(self):
        # Contenedor prinicipal
        contenedor = ttk.Frame(self.raiz, padding=20)
        contenedor.pack(fill="both", expand=True)

        ttk.Label(
            contenedor,
            text="FlashFood - Gestión de Productos",
            font=("Arial", 18, "bold")
        ).pack(anchor="w", pady=(0, 20))

        # Formulario
        formulario = ttk.Frame(contenedor)
        formulario.pack(fill="x")

        ttk.Label(formulario, text="Nombre:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        entrada_nombre = ttk.Entry(
            formulario, textvariable=self.nombre
        )
        entrada_nombre.grid(row=0, column=1, sticky="ew", padx=10)

        ttk.Label(formulario, text="Precio ($):").grid(
            row=1, column=0, sticky="w", pady=5
        )
        entrada_precio = ttk.Entry(
            formulario, textvariable=self.precio
        )
        entrada_precio.grid(row=1, column=1, sticky="ew", padx=10)

        ttk.Label(formulario, text="Stock:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        entrada_stock = ttk.Entry(
            formulario, textvariable=self.stock
        )
        entrada_stock.grid(row=2, column=1, sticky="ew", padx=10)

        formulario.columnconfigure(1, weight=1)

        # Botón para agregar productos
        ttk.Button(
            formulario,
            text="Agregar producto",
            command=self.agrega_producto
        ).grid(row=3, column=1, sticky="e", padx=10, pady=15)

        # Tabla
        self.tabla = ttk.Treeview(
            contenedor,
            columns=("nombre", "precio", "stock"),
            show="headings"
        )

        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("precio", text="Precio ($)")
        self.tabla.heading("stock", text="Stock")

        self.tabla.column("nombre", width=300)
        self.tabla.column("precio", width=120, anchor="e")
        self.tabla.column("stock", width=100, anchor="center")

        self.tabla.pack(fill="both", expand=True)

        entrada_nombre.focus_set()
    
    def agrega_producto(self):
        nombre = self.nombre.get().strip()

        if not nombre:
            messagebox.showwarning(
                "Dato faltante",
                "Ingresa el nombre del producto"
            )
            return

        try:
            precio = float(self.precio.get())
            stock = int(self.stock.get())

            if precio <= 0:
                raise ValueError

            if stock < 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Datos inválidos",
                "Ingresa un precio numérico mayor que cero "
                "y un stock entero mayor o igual a cero."
            )
            return

        self.tabla.insert(
            "",
            "end",
            values=(nombre, f"{precio:.2f}", stock)
        )

        self.nombre.set("")
        self.precio.set("")
        self.stock.set("0")

def main():
    raiz = tk.Tk()
    VentanaFlashFood(raiz)
    raiz.mainloop()

if __name__ == "__main__":
    main()