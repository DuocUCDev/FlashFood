"""Texto de dinero en pesos chilenos, sin decimales."""


def pesos(valor: int) -> str:
    return "$" + f"{valor:,}".replace(",", ".")
