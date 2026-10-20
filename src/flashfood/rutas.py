"""Ubicación de los JSON de la aplicación."""

from pathlib import Path


def directorio_datos() -> Path:
    actual = Path.cwd() / "data"
    if (actual / "productos.json").exists():
        return actual
    raiz = Path(__file__).resolve().parents[2]
    empaquetado = raiz / "data"
    if (empaquetado / "productos.json").exists():
        return empaquetado
    return actual
