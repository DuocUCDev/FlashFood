"""Validaciones compartidas por el modelo. No dependen de la interfaz."""

from flashfood.modelo.errores import ReglaNegocioError


def texto_obligatorio(valor: object, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ReglaNegocioError(f"{campo} es obligatorio")
    return valor.strip()


def booleano(valor: object, campo: str) -> bool:
    if type(valor) is not bool:
        raise ReglaNegocioError(f"{campo} debe ser sí o no")
    return valor


def exigir_entero(valor: object, campo: str, minimo: int) -> int:
    if type(valor) is not int:
        raise ReglaNegocioError(f"{campo} debe ser un número entero")
    if valor < minimo:
        if minimo == 1:
            raise ReglaNegocioError(f"{campo} debe ser un entero mayor que cero")
        if minimo == 0:
            raise ReglaNegocioError(f"{campo} debe ser un entero mayor o igual a cero")
        raise ReglaNegocioError(f"{campo} debe ser un entero mayor o igual a {minimo}")
    return valor
