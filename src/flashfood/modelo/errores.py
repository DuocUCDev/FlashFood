"""Errores de negocio y de persistencia. No dependen de la interfaz."""


class ReglaNegocioError(ValueError):
    """Una operación viola las reglas de FlashFood."""


class PersistenciaError(RuntimeError):
    """No se pudo leer o escribir los datos locales."""
