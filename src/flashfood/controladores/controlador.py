"""Traduce la interfaz al modelo. No dibuja ventanas ni decide el stock."""

from pathlib import Path

from flashfood.modelo.errores import ReglaNegocioError
from flashfood.modelo.pago import PagoBilletera, PagoEfectivo, PagoTarjeta, PagoTransferencia, ResultadoPago
from flashfood.modelo.pedido import EstadoPedido
from flashfood.modelo.sistema import FlashFood
from flashfood.persistencia.repositorio_json import RepositorioJSON
from flashfood.rutas import directorio_datos


class Controlador:
    def __init__(self, directorio: str | Path | None = None):
        self._directorio = Path(directorio) if directorio is not None else directorio_datos()
        self._sistema = FlashFood(RepositorioJSON(self._directorio))

    @property
    def directorio(self) -> Path:
        return self._directorio

    @property
    def advertencia(self) -> str:
        return "\n".join(self._sistema.advertencias)

    @property
    def hora_punta(self) -> bool:
        return self._sistema.hora_punta

    @property
    def lluvia(self) -> bool:
        return self._sistema.lluvia

    def definir_condiciones(self, hora_punta: bool, lluvia: bool) -> None:
        self._sistema.definir_condiciones(hora_punta, lluvia)

    def reglas(self) -> str:
        return self._sistema.texto_operacion()

    def resumen(self) -> dict:
        pedidos = self._sistema.listar_pedidos()
        repartidores = self._sistema.listar_repartidores()
        return {
            "productos": len(self._sistema.listar_productos()),
            "clientes": len(self._sistema.listar_clientes()),
            "repartidores": len(repartidores),
            "disponibles": sum(1 for item in repartidores if item.disponible),
            "pedidos": {
                estado.etiqueta: sum(1 for pedido in pedidos if pedido.estado is estado)
                for estado in EstadoPedido
            },
        }

    def listar_productos(self):
        return self._sistema.listar_productos()

    def listar_clientes(self):
        return self._sistema.listar_clientes()

    def listar_repartidores(self):
        return self._sistema.listar_repartidores()

    def listar_pedidos(self):
        return self._sistema.listar_pedidos()

    def obtener_producto(self, producto_id: str):
        return self._sistema.obtener_producto(producto_id)

    def obtener_cliente(self, cliente_id: str):
        return self._sistema.obtener_cliente(cliente_id)

    def obtener_repartidor(self, repartidor_id: str):
        return self._sistema.obtener_repartidor(repartidor_id)

    def obtener_pedido(self, pedido_id: str):
        return self._sistema.obtener_pedido(pedido_id)

    def nombre_cliente(self, cliente_id: str) -> str:
        try:
            return self._sistema.obtener_cliente(cliente_id).nombre
        except ReglaNegocioError:
            return "Cliente no disponible"

    def nombre_repartidor(self, repartidor_id: str | None) -> str:
        if not repartidor_id:
            return "Sin asignar"
        try:
            return self._sistema.obtener_repartidor(repartidor_id).nombre
        except ReglaNegocioError:
            return "Repartidor no disponible"

    def stock_disponible(self, producto_id: str) -> int:
        return self._sistema.stock_disponible(producto_id)

    def acciones(self, pedido_id: str) -> dict[str, bool]:
        return self._sistema.acciones(pedido_id)

    def registrar_producto(self, tipo: str, nombre: str, precio: str, stock: str, extra: str):
        return self._sistema.registrar_producto(
            tipo.strip(),
            nombre,
            self._entero(precio, "Precio", 1),
            self._entero(stock, "Stock", 0),
            self._extra(tipo, extra),
        )

    def editar_producto(self, producto_id: str, nombre: str, precio: str, stock: str, extra: str):
        self._exigir(producto_id, "un producto")
        return self._sistema.editar_producto(
            producto_id,
            nombre,
            self._entero(precio, "Precio", 1),
            self._entero(stock, "Stock", 0),
            self._extra_de_producto(producto_id, extra),
        )

    def eliminar_producto(self, producto_id: str) -> None:
        self._exigir(producto_id, "un producto")
        self._sistema.eliminar_producto(producto_id)

    def registrar_cliente(self, nombre: str, telefono: str, direccion: str, es_vip: bool):
        if type(es_vip) is not bool:
            raise ReglaNegocioError("El indicador VIP debe ser sí o no")
        return self._sistema.registrar_cliente(nombre, telefono, direccion, es_vip)

    def editar_cliente(self, cliente_id: str, nombre: str, telefono: str, direccion: str, es_vip: bool):
        self._exigir(cliente_id, "un cliente")
        if type(es_vip) is not bool:
            raise ReglaNegocioError("El indicador VIP debe ser sí o no")
        return self._sistema.editar_cliente(cliente_id, nombre, telefono, direccion, es_vip)

    def eliminar_cliente(self, cliente_id: str) -> None:
        self._exigir(cliente_id, "un cliente")
        self._sistema.eliminar_cliente(cliente_id)

    def registrar_repartidor(self, nombre: str, vehiculo: str):
        return self._sistema.registrar_repartidor(nombre, vehiculo)

    def editar_repartidor(self, repartidor_id: str, nombre: str, vehiculo: str):
        self._exigir(repartidor_id, "un repartidor")
        return self._sistema.editar_repartidor(repartidor_id, nombre, vehiculo)

    def eliminar_repartidor(self, repartidor_id: str) -> None:
        self._exigir(repartidor_id, "un repartidor")
        self._sistema.eliminar_repartidor(repartidor_id)

    def crear_pedido(self, cliente_id: str):
        self._exigir(cliente_id, "un cliente")
        return self._sistema.crear_pedido(cliente_id)

    def agregar_producto(self, pedido_id: str, producto_id: str, cantidad: str):
        self._exigir(pedido_id, "un pedido")
        self._exigir(producto_id, "un producto")
        return self._sistema.agregar_producto(
            pedido_id,
            producto_id,
            self._entero(cantidad, "Cantidad", 1),
        )

    def quitar_producto(self, pedido_id: str, producto_id: str):
        self._exigir(pedido_id, "un pedido")
        self._exigir(producto_id, "un producto del pedido")
        return self._sistema.quitar_producto(pedido_id, producto_id)

    def pagar(
        self,
        pedido_id: str,
        medio: str,
        rechazar: bool,
        monto: str,
        saldo: str,
        operacion: str,
    ) -> ResultadoPago:
        self._exigir(pedido_id, "un pedido")
        if type(rechazar) is not bool:
            raise ReglaNegocioError("La simulación del pago debe ser sí o no")
        return self._sistema.pagar(pedido_id, self._medio(medio, rechazar, monto, saldo, operacion))

    def preparar(self, pedido_id: str):
        self._exigir(pedido_id, "un pedido")
        return self._sistema.preparar(pedido_id)

    def asignar_repartidor(self, pedido_id: str, repartidor_id: str):
        self._exigir(pedido_id, "un pedido")
        self._exigir(repartidor_id, "un repartidor")
        return self._sistema.asignar_repartidor(pedido_id, repartidor_id)

    def despachar(self, pedido_id: str):
        self._exigir(pedido_id, "un pedido")
        return self._sistema.despachar(pedido_id)

    def entregar(self, pedido_id: str):
        self._exigir(pedido_id, "un pedido")
        return self._sistema.entregar(pedido_id)

    def cancelar(self, pedido_id: str):
        self._exigir(pedido_id, "un pedido")
        return self._sistema.cancelar(pedido_id)

    def _extra(self, tipo: str, extra: str):
        clave = tipo.strip()
        if clave == "Bebida":
            return self._entero(extra, "Mililitros", 1)
        if clave == "Comida":
            return extra
        raise ReglaNegocioError("El producto debe ser comida o bebida")

    def _extra_de_producto(self, producto_id: str, extra: str):
        producto = self._sistema.obtener_producto(producto_id)
        if producto.tipo == "bebida":
            return self._entero(extra, "Mililitros", 1)
        return extra

    def _medio(self, medio: str, rechazar: bool, monto: str, saldo: str, operacion: str):
        clave = medio.strip().lower()
        if clave == "tarjeta":
            return PagoTarjeta(aprobado=not rechazar)
        if clave == "efectivo":
            return PagoEfectivo(self._entero(monto, "Monto recibido", 1))
        if clave in {"billetera", "billetera digital"}:
            return PagoBilletera(self._entero(saldo, "Saldo", 0))
        if clave == "transferencia":
            return PagoTransferencia(operacion, aprobado=not rechazar)
        raise ReglaNegocioError("Selecciona un medio de pago")

    def _exigir(self, valor: str, campo: str) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ReglaNegocioError(f"Selecciona {campo}")
        return valor.strip()

    def _entero(self, texto: str, campo: str, minimo: int) -> int:
        if not isinstance(texto, str):
            raise ReglaNegocioError(f"{campo} debe ser un número entero")
        limpio = texto.strip()
        negativo = limpio.startswith("-")
        digitos = limpio[1:] if negativo else limpio
        if not digitos.isdigit():
            raise ReglaNegocioError(f"{campo} debe ser un número entero, sin puntos ni comas")
        valor = int(digitos) * (-1 if negativo else 1)
        if valor < minimo:
            if minimo == 1:
                raise ReglaNegocioError(f"{campo} debe ser un entero mayor que cero")
            raise ReglaNegocioError(f"{campo} debe ser un entero mayor o igual a cero")
        return valor
