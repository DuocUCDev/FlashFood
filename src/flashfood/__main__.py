"""Arranque de la aplicación de escritorio."""

import tkinter as tk
from tkinter import messagebox

from flashfood.modelo.errores import PersistenciaError


def main() -> None:
    try:
        from flashfood.vista.aplicacion import iniciar

        iniciar()
    except PersistenciaError as error:
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror("FlashFood", str(error))
        raiz.destroy()


if __name__ == "__main__":
    main()
