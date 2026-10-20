# Guía docente de FlashFood

## Objetivo

Modelar la Operación 13:00 con clases, encapsulamiento, abstracción, herencia, polimorfismo y composición. Las reglas viven en el modelo. Tkinter solo presenta datos y envía acciones al controlador. JSON guarda y recupera el estado.

## Secuencia sugerida

1. **Negocio.** Recorrer productos, clientes, pedidos, pagos y repartidores. Dibujar `CREADO → PAGADO → EN_PREPARACION → EN_CAMINO → ENTREGADO` y la salida a `CANCELADO`.
2. **Modelo.** Leer `Producto`, `Comida`, `Bebida`, `DetallePedido` y `Pedido`. Calcular subtotal, descuento VIP, despacho de hora punta y recargo por lluvia.
3. **Estados.** Intentar entregar un pedido creado y pagar dos veces. El error sale de `Pedido`, no de la ventana.
4. **Pagos.** Comparar `PagoTarjeta`, `PagoEfectivo` y `PagoBilletera`. Agregar una prueba con `PagoTransferencia` sin tocar las otras clases. Un rechazo no baja el stock.
5. **Reparto y cancelación.** Asignar el mismo repartidor a dos pedidos en preparación. Cancelar uno pagado y comprobar que el stock vuelve una sola vez.
6. **MVC y JSON.** Seguir un clic desde la vista hasta `Controlador`, `FlashFood` y `RepositorioJSON`. Cerrar y volver a abrir: el stock no se descuenta otra vez.
7. **Escritorio.** Ejecutar `flashfood` y completar el flujo en las ocho pantallas. Los `messagebox` muestran el error y la ventana sigue abierta.

## Qué mirar en la evaluación

| Criterio | Dónde comprobarlo |
| --- | --- |
| Cuatro pilares | `Producto`, `MetodoPago` y sus subclases; `Pedido.cobrar` |
| Reglas de negocio | `tests/test_flashfood.py` |
| Tkinter y ttk | `src/flashfood/vista/`, menú Módulos y `Treeview` |
| MVC | modelo sin Tkinter; vistas sin descontar stock |
| JSON | carpeta `data/` y la prueba de recarga |
| Validaciones | formularios del controlador y errores del modelo |

Preguntas útiles: ¿por qué el estado no tiene setter? ¿Qué archivo hay que tocar para sumar un medio de pago? ¿Por qué el precio de la línea no cambia si después cambia el catálogo? ¿En qué estados se puede cancelar y cuándo vuelve el stock?
