"""Repartidor y su disponibilidad para una sola entrega activa."""

from flashfood.modelo.errores import ReglaNegocioError
from flashfood.modelo.validacion import booleano, texto_obligatorio


class Repartidor:
    def __init__(self, id: str, nombre: str, vehiculo: str, disponible: bool = True):
        self._id = texto_obligatorio(id, "Identificador")
        self._nombre = texto_obligatorio(nombre, "Nombre")
        self._vehiculo = texto_obligatorio(vehiculo, "Vehículo")
        self._disponible = booleano(disponible, "La disponibilidad")

    @property
    def id(self) -> str:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def vehiculo(self) -> str:
        return self._vehiculo

    @property
    def disponible(self) -> bool:
        return self._disponible

    def establecer_disponibilidad(self, disponible: bool) -> None:
        self._disponible = booleano(disponible, "La disponibilidad")

    def actualizar(self, nombre: str, vehiculo: str) -> None:
        nombre_limpio = texto_obligatorio(nombre, "Nombre")
        vehiculo_limpio = texto_obligatorio(vehiculo, "Vehículo")
        self._nombre = nombre_limpio
        self._vehiculo = vehiculo_limpio

    def a_diccionario(self) -> dict:
        return {"id": self._id, "nombre": self._nombre, "vehiculo": self._vehiculo}

    @classmethod
    def desde_diccionario(cls, datos: dict) -> "Repartidor":
        try:
            return cls(str(datos["id"]), datos["nombre"], datos["vehiculo"])
        except (KeyError, TypeError) as error:
            raise ReglaNegocioError("Repartidor guardado incompleto") from error

    def __repr__(self) -> str:
        return f"Repartidor({self._nombre!r}, disponible={self._disponible})"
