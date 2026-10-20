# FlashFood — Operación 13:00

Aplicación de escritorio para administrar productos, clientes, pedidos, pagos y repartidores de FlashFood. El caso aplica abstracción, encapsulamiento, herencia y polimorfismo, con arquitectura MVC y persistencia en JSON.

## Ejecutar

Requiere Python 3.12 o superior. Desde la carpeta del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
flashfood
```

En Windows: `.venv\Scripts\Activate.ps1`.

La ventana abre los datos de `data/`. Cada operación vuelve a guardar productos, clientes, repartidores, pedidos y las condiciones de despacho.

```bash
python -m unittest discover -s tests -v
flashfood-demo
```

`flashfood-demo` recorre registro, pago rechazado, pago aprobado, preparación, despacho y entrega sin abrir ventanas.

## Pantallas

Inicio, Productos, Clientes, Pedidos, Detalle del pedido, Pagos, Repartidores y Seguimiento. El menú **Módulos** cambia de pantalla. Las tablas usan `ttk.Treeview` y los avisos usan `messagebox`.

## Estados

```text
CREADO → PAGADO → EN_PREPARACION → EN_CAMINO → ENTREGADO
   └──────────────→ CANCELADO
```

Se puede cancelar en Creado, Pagado y En preparación. En camino y Entregado no se cancelan. El pedido entregado no vuelve a cambiar.

## Reglas

1. No se agrega una cantidad mayor que el stock disponible, contando lo ya comprometido en otros pedidos creados.
2. El stock nunca queda negativo.
3. Un pedido puede tener varias líneas. El precio de cada línea queda congelado al agregarla.
4. El total es subtotal − descuento + despacho. El despacho base es $2.000. En hora punta sube 25%. Con lluvia se suman $1.000. Un cliente VIP tiene 10% de descuento sobre el subtotal.
5. Un pedido no se paga dos veces. Un pago rechazado no confirma la compra ni descuenta inventario.
6. El stock se descuenta solo cuando el pago queda aprobado, y una sola vez. Si ese descuento no puede completarse, el cobro se anula.
7. Cancelar un pedido pagado restituye el stock una sola vez y libera al repartidor si ya estaba asignado.
8. Un repartidor no tiene dos entregas activas. Se asigna con el pedido en preparación y queda libre al entregar o al cancelar.
9. Una operación inválida muestra el error y la aplicación sigue abierta.

## Pilares de POO

| Pilar | Dónde se ve |
| --- | --- |
| Abstracción | `Producto` y `MetodoPago` son clases abstractas (`abc`). No se instancian. |
| Encapsulamiento | El estado, el stock y el pago se cambian con métodos. No hay setters públicos. |
| Herencia | `Comida` y `Bebida` especializan `Producto`. `PagoTarjeta`, `PagoEfectivo`, `PagoBilletera` y `PagoTransferencia` especializan `MetodoPago`. |
| Polimorfismo | `Pedido.cobrar` llama a `procesar` sin saber qué medio concreto recibió. |
| Composición | Un `Pedido` contiene varios `DetallePedido`. |

`PagoTransferencia` se agregó implementando `MetodoPago`. Las otras clases de pago no se modifican para aceptarla.

## Estructura

```text
src/flashfood/modelo/          entidades, reglas y FlashFood
src/flashfood/persistencia/    lectura y escritura JSON
src/flashfood/controladores/   traducción de la interfaz al modelo
src/flashfood/vista/           ventanas Tkinter y ttk
data/                          datos de ejemplo
tests/                         reglas, persistencia y recorrido de pantallas
```

El modelo no importa Tkinter. Las pantallas no deciden stock, totales ni transiciones.

## Documentación

- [Diagrama de clases](docs/diagrama-uml.md)
- [Guía docente](docs/guia-docente.md)
- [Especificación](FlashFood_Operacion_1300_Requerimientos.md)
