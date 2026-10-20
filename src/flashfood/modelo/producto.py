"""Productos del catálogo. Comida y Bebida especializan un producto abstracto."""

from abc import ABC, abstractmethod

from flashfood.modelo.errores import ReglaNegocioError
from flashfood.modelo.validacion import exigir_entero, texto_obligatorio


class Producto(ABC):
    """Nombre, precio y stock comunes. El stock no puede quedar negativo."""

    def __init__(self, id: str, nombre: str, precio: int, stock: int):
        self._id = texto_obligatorio(id, "Identificador")
        self._nombre = texto_obligatorio(nombre, "Nombre")
        self._precio = exigir_entero(precio, "Precio", minimo=1)
        self._stock = exigir_entero(stock, "Stock", minimo=0)

    @property
    def id(self) -> str:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def precio(self) -> int:
        return self._precio

    @property
    def stock(self) -> int:
        return self._stock

    @property
    @abstractmethod
    def tipo(self) -> str:
        """Clave estable para guardar el producto."""

    @property
    def tipo_visible(self) -> str:
        return "Comida" if self.tipo == "comida" else "Bebida"

    @property
    @abstractmethod
    def detalle(self) -> str:
        """Dato propio de la comida o de la bebida."""

    def actualizar(self, nombre: str, precio: int, stock: int) -> None:
        nombre_limpio = texto_obligatorio(nombre, "Nombre")
        precio_limpio = exigir_entero(precio, "Precio", minimo=1)
        stock_limpio = exigir_entero(stock, "Stock", minimo=0)
        self._nombre = nombre_limpio
        self._precio = precio_limpio
        self._stock = stock_limpio

    def descontar(self, cantidad: int) -> None:
        cantidad_valida = exigir_entero(cantidad, "Cantidad", minimo=1)
        if cantidad_valida > self._stock:
            raise ReglaNegocioError(
                f"Stock insuficiente de {self._nombre}. Disponible: {self._stock}"
            )
        self._stock -= cantidad_valida

    def reponer(self, cantidad: int) -> None:
        self._stock += exigir_entero(cantidad, "Cantidad", minimo=1)

    @abstractmethod
    def actualizar_especifico(self, extra: object) -> None:
        """Actualiza la categoría o los mililitros."""

    def a_diccionario(self) -> dict:
        datos = {
            "id": self._id,
            "tipo": self.tipo,
            "nombre": self._nombre,
            "precio": self._precio,
            "stock": self._stock,
        }
        datos.update(self._extras())
        return datos

    @abstractmethod
    def _extras(self) -> dict:
        """Campos propios de la subclase."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._nombre!r}, {self._precio}, stock={self._stock})"


class Comida(Producto):
    def __init__(self, id: str, nombre: str, precio: int, stock: int, categoria: str):
        super().__init__(id, nombre, precio, stock)
        self._categoria = texto_obligatorio(categoria, "Categoría")

    @property
    def tipo(self) -> str:
        return "comida"

    @property
    def categoria(self) -> str:
        return self._categoria

    @property
    def detalle(self) -> str:
        return self._categoria

    def actualizar_especifico(self, extra: object) -> None:
        self._categoria = texto_obligatorio(extra, "Categoría")

    def _extras(self) -> dict:
        return {"categoria": self._categoria}


class Bebida(Producto):
    def __init__(self, id: str, nombre: str, precio: int, stock: int, mililitros: int):
        super().__init__(id, nombre, precio, stock)
        self._mililitros = exigir_entero(mililitros, "Mililitros", minimo=1)

    @property
    def tipo(self) -> str:
        return "bebida"

    @property
    def mililitros(self) -> int:
        return self._mililitros

    @property
    def detalle(self) -> str:
        return f"{self._mililitros} ml"

    def actualizar_especifico(self, extra: object) -> None:
        self._mililitros = exigir_entero(extra, "Mililitros", minimo=1)

    def _extras(self) -> dict:
        return {"mililitros": self._mililitros}


def producto_desde_diccionario(datos: dict) -> Producto:
    if not isinstance(datos, dict):
        raise ReglaNegocioError("El producto guardado no tiene el formato esperado")
    try:
        tipo = datos["tipo"]
        identificador = str(datos["id"])
        if tipo == "comida":
            return Comida(
                identificador,
                datos["nombre"],
                datos["precio"],
                datos["stock"],
                datos["categoria"],
            )
        if tipo == "bebida":
            return Bebida(
                identificador,
                datos["nombre"],
                datos["precio"],
                datos["stock"],
                datos["mililitros"],
            )
    except KeyError as error:
        raise ReglaNegocioError("Producto guardado incompleto") from error
    raise ReglaNegocioError("Tipo de producto desconocido")
