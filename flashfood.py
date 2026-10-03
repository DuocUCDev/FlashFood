from abc import ABC, abstractclassmethod, abstractmethod
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


# VALIDACIONES
def validar_enterno(valor, nombre, minimo=0):
    """Evita negativos, decimales y valores booleanos."""
    if type(valor) is not int or valor < minimo:
        raise ValueError(
            f"{nombre} debe ser un entero mayor o igual a {minimo}."
        )
    return valor

# 1. ABASTRACCIONES Y ENCAPSULAMIENTOS
class Producto(ABC):
    """
    Clase abstracta.
    Define los atributos  y comportamientos comunes de 
    los productos. No se puede instaciar directemante.
    """

    def __init__(self, codigo, nombre, precio, stock):
        if not codigo.strip() or not nombre.strip():
            raise ValueError("Código y nombre son obligatorios.")
        self._codigo = codigo
        self._nombre = nombre
        self.precio = precio
        self._stock = validar_enterno(stock, "Stock")

    @property
    def codigo(self):
        return self._codigo

    @property
    def nombre(self):
        return self._nombre

    @property
    def precio(self):
        return self._precio

    @precio.setter
    def precio(self, nuevo_precio):
        self._precio = validar_enterno(nuevo_precio, "Precio", minimo=1)

    @property
    def stock(self):
        return self._stock

    def reponer_stock(self, cantidad):
        validar_enterno(cantidad, "Cantidad", minimo=1)
        self._stock += cantidad

    def descontar_stock(self, cantidad):
        validar_enterno(cantidad, "Cantidad", minimo=1)

        if cantidad > self._stock:
            raise ValueError(f"Stock insuficiente de {self._nombre}")
        
        self._stock -= cantidad

    @abstractmethod
    def descripcion(self):
        """Cada subclase implementa su descripción."""
        pass

    def __str__(self):
        return {
            f"{self.codigo} | {self.descripcion()} | "
            f"${self.precio:,} | Stock: {self.stock}"
        }

# 2. HERENCIAS Y POLIMORFISMO
def Comida(Producto):
    def __init__(
            self,
            codigo,
            nombre,
            precio,
            stock,
            tiempo_preparacion
        ):
        super().__init__(codigo, nombre, precio, stock)

        self._tiempo_preparacion = validar_enterno(tiempo_preparacion, "Tiempo de preparacion", minimo=1)

    @property
    def tiempo_preparacion(self):
        return self._tiempo_preparacion

    def descripcion(self):
        return {
            f"{self.nombre} "
            f"({self.tiempo_preparacion} minutos)"
        }

def Bebida(Producto):
    def __init__(
            self,
            codigo,
            nombre,
            precio,
            stock,
            volumen_ml
        ):
        super().__init__(codigo, nombre, precio, stock)

        self._volumen_ml = validar_enterno(tiempo_preparacion, "Volumen", minimo=1)

    @property
    def volumen_ml(self):
        return self._volumen_ml

    def descripcion(self):
        return {
            f"{self.nombre} "
            f"({self.volumen_ml} ml)"
        }