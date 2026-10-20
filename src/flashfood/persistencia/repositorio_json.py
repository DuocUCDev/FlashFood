"""Lectura y escritura JSON, separadas de las ventanas y de las reglas."""

import json
from pathlib import Path

from flashfood.modelo.errores import PersistenciaError


class RepositorioJSON:
    def __init__(self, directorio: str | Path):
        self.directorio = Path(directorio)
        self.advertencias: list[str] = []
        self._archivos_danados: set[str] = set()
        try:
            self.directorio.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise PersistenciaError(f"No se pudo preparar la carpeta de datos: {error}") from error

    def cargar_lista(self, nombre: str) -> list:
        datos = self._leer(nombre)
        if datos is None:
            return []
        if not isinstance(datos, list):
            self.advertencias.append(f"{nombre}.json debía contener una lista y se ignoró.")
            self._archivos_danados.add(nombre)
            return []
        return datos

    def cargar_objeto(self, nombre: str) -> dict:
        datos = self._leer(nombre)
        if datos is None:
            return {}
        if not isinstance(datos, dict):
            self.advertencias.append(f"{nombre}.json debía contener un objeto y se ignoró.")
            self._archivos_danados.add(nombre)
            return {}
        return datos

    def guardar(self, nombre: str, datos: list | dict) -> None:
        if self._archivos_danados:
            danados = ", ".join(f"{item}.json" for item in sorted(self._archivos_danados))
            raise PersistenciaError(
                f"Hay archivos dañados ({danados}). Restaura los respaldos .bak antes de guardar."
            )
        ruta = self.directorio / f"{nombre}.json"
        temporal = self.directorio / f"{nombre}.json.tmp"
        try:
            temporal.write_text(
                json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporal.replace(ruta)
        except OSError as error:
            raise PersistenciaError(f"No se pudo guardar {nombre}.json: {error}") from error

    def _leer(self, nombre: str):
        ruta = self.directorio / f"{nombre}.json"
        if not ruta.exists():
            return None
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._respaldar(ruta)
            self._archivos_danados.add(nombre)
            self.advertencias.append(
                f"No se pudo leer {ruta.name}. Se dejó una copia {ruta.name}.bak y esos datos no se cargaron."
            )
            return None

    def _respaldar(self, ruta: Path) -> None:
        destino = ruta.with_name(ruta.name + ".bak")
        try:
            if destino.exists():
                destino.unlink()
            ruta.replace(destino)
        except OSError:
            self.advertencias.append(f"No se pudo respaldar {ruta.name}.")
