"""FlashFood coordina catálogo, clientes, pedidos, pagos y repartidores.

Las ventanas no viven aquí: esta clase solo aplica reglas y usa el repositorio.
"""

from uuid import uuid4

from flashfood.modelo.cliente import Cliente
from flashfood.modelo.errores import ReglaNegocioError
from flashfood.modelo.pago import MetodoPago, ResultadoPago
from flashfood.modelo.pedido import EstadoPedido, Pedido
from flashfood.modelo.producto import Bebida, Comida, Producto, producto_desde_diccionario
from flashfood.modelo.repartidor import Repartidor
from flashfood.modelo.validacion import exigir_entero, texto_obligatorio
from flashfood.persistencia.repositorio_json import RepositorioJSON


class FlashFood:
    def __init__(self, repositorio: RepositorioJSON):
        self._repositorio = repositorio
        self._productos: dict[str, Producto] = {}
        self._clientes: dict[str, Cliente] = {}
        self._repartidores: dict[str, Repartidor] = {}
        self._pedidos: dict[str, Pedido] = {}
        self._hora_punta = False
        self._lluvia = False
        self.cargar()

    @property
    def hora_punta(self) -> bool:
        return self._hora_punta

    @property
    def lluvia(self) -> bool:
        return self._lluvia

    @property
    def advertencias(self) -> tuple[str, ...]:
        return tuple(self._repositorio.advertencias)

    def cargar(self) -> None:
        self._productos.clear()
        self._clientes.clear()
        self._repartidores.clear()
        self._pedidos.clear()
        for datos in self._repositorio.cargar_lista("productos"):
            self._incorporar(producto_desde_diccionario, datos, self._productos, "Producto")
        for datos in self._repositorio.cargar_lista("clientes"):
            self._incorporar(Cliente.desde_diccionario, datos, self._clientes, "Cliente")
        for datos in self._repositorio.cargar_lista("repartidores"):
            self._incorporar(Repartidor.desde_diccionario, datos, self._repartidores, "Repartidor")
        for datos in self._repositorio.cargar_lista("pedidos"):
            self._incorporar(Pedido.desde_diccionario, datos, self._pedidos, "Pedido")
        operacion = self._repositorio.cargar_objeto("operacion")
        self._hora_punta = operacion.get("hora_punta", False) is True
        self._lluvia = operacion.get("lluvia", False) is True
        self._sincronizar_repartidores()

    def guardar(self) -> None:
        self._repositorio.guardar("productos", [item.a_diccionario() for item in self._productos.values()])
        self._repositorio.guardar("clientes", [item.a_diccionario() for item in self._clientes.values()])
        self._repositorio.guardar("repartidores", [item.a_diccionario() for item in self._repartidores.values()])
        self._repositorio.guardar("pedidos", [item.a_diccionario() for item in self._pedidos.values()])
        self._repositorio.guardar(
            "operacion",
            {"hora_punta": self._hora_punta, "lluvia": self._lluvia},
        )

    def definir_condiciones(self, hora_punta: bool, lluvia: bool) -> None:
        if type(hora_punta) is not bool or type(lluvia) is not bool:
            raise ReglaNegocioError("Las condiciones de operación deben ser sí o no")
        self._hora_punta = hora_punta
        self._lluvia = lluvia
        self.guardar()

    def listar_productos(self) -> tuple[Producto, ...]:
        return tuple(self._productos.values())

    def listar_clientes(self) -> tuple[Cliente, ...]:
        return tuple(self._clientes.values())

    def listar_repartidores(self) -> tuple[Repartidor, ...]:
        return tuple(self._repartidores.values())

    def listar_pedidos(self) -> tuple[Pedido, ...]:
        return tuple(self._pedidos.values())

    def obtener_producto(self, producto_id: str) -> Producto:
        return self._buscar(self._productos, producto_id, "Producto inexistente")

    def obtener_cliente(self, cliente_id: str) -> Cliente:
        return self._buscar(self._clientes, cliente_id, "Cliente inexistente")

    def obtener_repartidor(self, repartidor_id: str) -> Repartidor:
        return self._buscar(self._repartidores, repartidor_id, "Repartidor inexistente")

    def obtener_pedido(self, pedido_id: str) -> Pedido:
        return self._buscar(self._pedidos, pedido_id, "Pedido inexistente")

    def stock_disponible(self, producto_id: str) -> int:
        producto = self.obtener_producto(producto_id)
        disponible = producto.stock - self._stock_comprometido(producto_id)
        return disponible if disponible > 0 else 0

    def acciones(self, pedido_id: str) -> dict[str, bool]:
        pedido = self.obtener_pedido(pedido_id)
        return {
            "puede_editar_items": pedido.estado is EstadoPedido.CREADO,
            "puede_pagar": pedido.estado is EstadoPedido.CREADO and bool(pedido.detalles),
            "puede_preparar": pedido.estado is EstadoPedido.PAGADO,
            "puede_asignar": pedido.estado is EstadoPedido.EN_PREPARACION and not pedido.repartidor_id,
            "puede_despachar": pedido.estado is EstadoPedido.EN_PREPARACION and bool(pedido.repartidor_id),
            "puede_entregar": pedido.estado is EstadoPedido.EN_CAMINO,
            "puede_cancelar": pedido.puede_cancelarse(),
        }

    def texto_operacion(self) -> str:
        return (
            f"{Pedido.texto_reglas()} "
            "Se puede cancelar en Creado, Pagado y En preparación. "
            "Un pedido entregado no cambia de estado. "
            "El stock se descuenta solo si el pago se aprueba y, si luego se cancela, se restituye una sola vez."
        )

    def registrar_producto(self, tipo: str, nombre: str, precio: int, stock: int, extra: object) -> Producto:
        identificador = self._nuevo_id("prod")
        if tipo == "Comida":
            producto: Producto = Comida(
                identificador, nombre, precio, stock, texto_obligatorio(extra, "Categoría")
            )
        elif tipo == "Bebida":
            producto = Bebida(
                identificador, nombre, precio, stock, exigir_entero(extra, "Mililitros", minimo=1)
            )
        else:
            raise ReglaNegocioError("El producto debe ser comida o bebida")
        self._rechazar_nombre_repetido(producto.nombre)
        self._productos[producto.id] = producto
        self.guardar()
        return producto

    def editar_producto(self, producto_id: str, nombre: str, precio: int, stock: int, extra: object) -> Producto:
        producto = self.obtener_producto(producto_id)
        stock_validado = exigir_entero(stock, "Stock", minimo=0)
        comprometido = self._stock_comprometido(producto_id)
        if stock_validado < comprometido:
            raise ReglaNegocioError(
                f"El stock no puede ser menor que lo reservado en pedidos creados ({comprometido})"
            )
        nombre_limpio = texto_obligatorio(nombre, "Nombre")
        self._rechazar_nombre_repetido(nombre_limpio, excepto=producto.id)
        if isinstance(producto, Comida):
            extra_validado = texto_obligatorio(extra, "Categoría")
        elif isinstance(producto, Bebida):
            extra_validado = exigir_entero(extra, "Mililitros", minimo=1)
        else:
            raise ReglaNegocioError("Producto no válido")
        producto.actualizar(nombre_limpio, precio, stock_validado)
        producto.actualizar_especifico(extra_validado)
        self.guardar()
        return producto

    def eliminar_producto(self, producto_id: str) -> None:
        if any(pedido.contiene(producto_id) for pedido in self._pedidos.values()):
            raise ReglaNegocioError("No se puede eliminar un producto que está en un pedido")
        self.obtener_producto(producto_id)
        del self._productos[producto_id]
        self.guardar()

    def registrar_cliente(self, nombre: str, telefono: str, direccion: str, es_vip: bool) -> Cliente:
        cliente = Cliente(self._nuevo_id("cli"), nombre, telefono, direccion, es_vip)
        self._clientes[cliente.id] = cliente
        self.guardar()
        return cliente

    def editar_cliente(self, cliente_id: str, nombre: str, telefono: str, direccion: str, es_vip: bool) -> Cliente:
        cliente = self.obtener_cliente(cliente_id)
        cliente.actualizar(nombre, telefono, direccion, es_vip)
        self.guardar()
        return cliente

    def eliminar_cliente(self, cliente_id: str) -> None:
        if any(pedido.cliente_id == cliente_id for pedido in self._pedidos.values()):
            raise ReglaNegocioError("No se puede eliminar un cliente que tiene pedidos")
        self.obtener_cliente(cliente_id)
        del self._clientes[cliente_id]
        self.guardar()

    def registrar_repartidor(self, nombre: str, vehiculo: str) -> Repartidor:
        repartidor = Repartidor(self._nuevo_id("rep"), nombre, vehiculo, True)
        self._repartidores[repartidor.id] = repartidor
        self.guardar()
        return repartidor

    def editar_repartidor(self, repartidor_id: str, nombre: str, vehiculo: str) -> Repartidor:
        repartidor = self.obtener_repartidor(repartidor_id)
        repartidor.actualizar(nombre, vehiculo)
        self.guardar()
        return repartidor

    def eliminar_repartidor(self, repartidor_id: str) -> None:
        if any(pedido.repartidor_id == repartidor_id for pedido in self._pedidos.values()):
            raise ReglaNegocioError("No se puede eliminar un repartidor asignado a un pedido")
        self.obtener_repartidor(repartidor_id)
        del self._repartidores[repartidor_id]
        self.guardar()

    def crear_pedido(self, cliente_id: str) -> Pedido:
        cliente = self.obtener_cliente(cliente_id)
        pedido = Pedido(self._nuevo_id("ped"), cliente.id, cliente.es_vip, self._hora_punta, self._lluvia)
        self._pedidos[pedido.id] = pedido
        self.guardar()
        return pedido

    def agregar_producto(self, pedido_id: str, producto_id: str, cantidad: int) -> Pedido:
        pedido = self.obtener_pedido(pedido_id)
        if pedido.estado is not EstadoPedido.CREADO:
            raise ReglaNegocioError("Solo se modifican los productos de un pedido creado")
        producto = self.obtener_producto(producto_id)
        cantidad = exigir_entero(cantidad, "Cantidad", minimo=1)
        disponible = self.stock_disponible(producto_id)
        if cantidad > disponible:
            raise ReglaNegocioError(
                f"No hay stock suficiente de {producto.nombre}. Disponible: {disponible}"
            )
        pedido.agregar(producto, cantidad)
        self.guardar()
        return pedido

    def quitar_producto(self, pedido_id: str, producto_id: str) -> Pedido:
        pedido = self.obtener_pedido(pedido_id)
        pedido.quitar(producto_id)
        self.guardar()
        return pedido

    def pagar(self, pedido_id: str, metodo: MetodoPago) -> ResultadoPago:
        pedido = self.obtener_pedido(pedido_id)
        pedido.validar_puede_pagarse()
        self._verificar_stock_fisico(pedido)
        resultado = pedido.cobrar(metodo)
        if not resultado.aprobado:
            return resultado
        aplicado = False
        try:
            self._descontar_pedido(pedido)
            aplicado = True
            pedido.confirmar_pago(resultado)
        except Exception:
            metodo.anular(resultado)
            if aplicado and not pedido.stock_descontado:
                self._reponer_pedido(pedido)
            raise
        self.guardar()
        return resultado

    def preparar(self, pedido_id: str) -> Pedido:
        pedido = self.obtener_pedido(pedido_id)
        pedido.preparar()
        self.guardar()
        return pedido

    def asignar_repartidor(self, pedido_id: str, repartidor_id: str) -> Pedido:
        pedido = self.obtener_pedido(pedido_id)
        repartidor = self.obtener_repartidor(repartidor_id)
        if not repartidor.disponible or self._repartidor_ocupado(repartidor.id):
            raise ReglaNegocioError(f"{repartidor.nombre} ya tiene una entrega en curso")
        pedido.asignar_repartidor(repartidor.id)
        repartidor.establecer_disponibilidad(False)
        self.guardar()
        return pedido

    def despachar(self, pedido_id: str) -> Pedido:
        pedido = self.obtener_pedido(pedido_id)
        pedido.despachar()
        self.guardar()
        return pedido

    def entregar(self, pedido_id: str) -> Pedido:
        pedido = self.obtener_pedido(pedido_id)
        repartidor = None
        if pedido.repartidor_id:
            repartidor = self.obtener_repartidor(pedido.repartidor_id)
        pedido.entregar()
        if repartidor is not None:
            repartidor.establecer_disponibilidad(True)
        self.guardar()
        return pedido

    def cancelar(self, pedido_id: str) -> Pedido:
        pedido = self.obtener_pedido(pedido_id)
        if not pedido.puede_cancelarse():
            raise ReglaNegocioError(f"No se puede cancelar un pedido {pedido.estado.etiqueta.lower()}")
        if pedido.stock_descontado and not pedido.stock_restituido:
            self._reponer_pedido(pedido)
            pedido.marcar_stock_restituido()
        self._liberar_repartidor(pedido)
        pedido.cancelar()
        self.guardar()
        return pedido

    def _verificar_stock_fisico(self, pedido: Pedido) -> None:
        for detalle in pedido.detalles:
            producto = self.obtener_producto(detalle.producto_id)
            if detalle.cantidad > producto.stock:
                raise ReglaNegocioError(f"Stock insuficiente de {producto.nombre}")

    def _descontar_pedido(self, pedido: Pedido) -> None:
        aplicados: list[tuple[Producto, int]] = []
        try:
            for detalle in pedido.detalles:
                producto = self.obtener_producto(detalle.producto_id)
                producto.descontar(detalle.cantidad)
                aplicados.append((producto, detalle.cantidad))
        except Exception:
            for producto, cantidad in reversed(aplicados):
                producto.reponer(cantidad)
            raise

    def _reponer_pedido(self, pedido: Pedido) -> None:
        productos = []
        for detalle in pedido.detalles:
            productos.append((self.obtener_producto(detalle.producto_id), detalle.cantidad))
        for producto, cantidad in productos:
            producto.reponer(cantidad)

    def _liberar_repartidor(self, pedido: Pedido) -> None:
        if not pedido.repartidor_id:
            return
        repartidor = self._repartidores.get(pedido.repartidor_id)
        if repartidor is not None:
            repartidor.establecer_disponibilidad(True)

    def _stock_comprometido(self, producto_id: str, excepto: Pedido | None = None) -> int:
        total = 0
        for pedido in self._pedidos.values():
            if pedido.estado is not EstadoPedido.CREADO or pedido is excepto:
                continue
            total += pedido.cantidad_de(producto_id)
        return total

    def _repartidor_ocupado(self, repartidor_id: str) -> bool:
        return any(
            pedido.repartidor_id == repartidor_id
            and pedido.estado in (EstadoPedido.EN_PREPARACION, EstadoPedido.EN_CAMINO)
            for pedido in self._pedidos.values()
        )

    def _sincronizar_repartidores(self) -> None:
        for repartidor in self._repartidores.values():
            repartidor.establecer_disponibilidad(not self._repartidor_ocupado(repartidor.id))

    def _incorporar(self, fabrica, datos: dict, destino: dict, etiqueta: str) -> None:
        try:
            entidad = fabrica(datos)
        except (ReglaNegocioError, KeyError, TypeError) as error:
            self._repositorio.advertencias.append(f"{etiqueta} omitido: {error}")
            return
        if entidad.id in destino:
            self._repositorio.advertencias.append(f"{etiqueta} duplicado omitido: {entidad.id}")
            return
        destino[entidad.id] = entidad

    def _buscar(self, coleccion: dict, identificador: str, mensaje: str):
        try:
            return coleccion[identificador]
        except KeyError as error:
            raise ReglaNegocioError(mensaje) from error

    def _rechazar_nombre_repetido(self, nombre: str, excepto: str | None = None) -> None:
        normalizado = nombre.strip().lower()
        if any(item.nombre.lower() == normalizado and item.id != excepto for item in self._productos.values()):
            raise ReglaNegocioError("Ya existe un producto con ese nombre")

    @staticmethod
    def _nuevo_id(prefijo: str) -> str:
        return f"{prefijo}-{uuid4().hex[:8]}"
