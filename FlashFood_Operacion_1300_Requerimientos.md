# FlashFood — Operación 13:00

**Caso práctico de Programación Orientada a Objetos (POO) con Python**  
**Aplicación de escritorio:** Tkinter + ttk  
**Persistencia:** JSON  
**Arquitectura:** Modelo–Vista–Controlador (MVC)

## 1. Contexto del caso

FlashFood es una empresa de comida rápida que recibe pedidos a domicilio, especialmente durante el horario de almuerzo.

Son las 12:30 y el equipo de FlashFood se prepara para enfrentar la mayor demanda del día: la **Operación 13:00**.

Durante este periodo, los clientes realizan pedidos que pueden incluir distintas comidas y bebidas. Cada pedido debe validarse, pagarse, prepararse y asignarse a un repartidor para su entrega.

Actualmente, la empresa necesita un sistema que permita administrar estos procesos de manera ordenada, evitando errores como vender productos sin stock, cobrar dos veces un pedido o asignar un mismo repartidor a entregas simultáneas.

**Desafío:** diseñar e implementar una aplicación de escritorio en Python, con interfaz gráfica, que gestione productos, clientes, pedidos, pagos y repartidores aplicando POO, reglas de negocio, MVC y persistencia local.

## 2. Objetivo general

Diseñar e implementar una aplicación de escritorio que simule la operación de FlashFood y aplique **abstracción, encapsulamiento, herencia y polimorfismo**, separando la lógica de negocio de la interfaz gráfica.

## 3. Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3.12 o superior | Lenguaje principal |
| Tkinter | Interfaz gráfica de escritorio |
| tkinter.ttk | Componentes como tablas, pestañas, formularios y botones |
| JSON (biblioteca estándar) | Persistencia local |
| POO | Modelado de entidades y reglas de negocio |
| MVC | Separación de responsabilidades |
| VS Code o PyCharm | Entorno de desarrollo, a elección |
| Git | Control de versiones |

> Tkinter y ttk forman parte normalmente de la distribución estándar de Python. Se eligieron por su accesibilidad para la enseñanza; no se afirma que sean las bibliotecas gráficas más utilizadas en todos los contextos.

## 4. Requerimientos funcionales

| Código | Módulo | Requerimiento |
|---|---|---|
| RF01 | Productos | Registrar comidas y bebidas con nombre, precio y stock. |
| RF02 | Inventario | Consultar disponibilidad y evitar stock negativo. |
| RF03 | Clientes | Registrar información de clientes. |
| RF04 | Pedidos | Crear pedidos asociados a un cliente. |
| RF05 | Pedidos | Incorporar varios productos y cantidades a un pedido. |
| RF06 | Cálculos | Calcular subtotal, costo de despacho y total. |
| RF07 | Pagos | Implementar pagos con tarjeta, billetera digital y efectivo. |
| RF08 | Pagos | Simular aprobación o rechazo de pagos. |
| RF09 | Estados | Administrar el ciclo de vida de los pedidos. |
| RF10 | Repartidores | Registrar y asignar repartidores disponibles. |
| RF11 | Inventario | Descontar stock al confirmar un pago aprobado. |
| RF12 | Cancelaciones | Cancelar pedidos y restituir stock cuando corresponda. |
| RF13 | Validaciones | Impedir pagos duplicados y operaciones inválidas. |
| RF14 | Interfaz gráfica | Realizar las operaciones mediante ventanas, formularios, botones y tablas sin depender de la consola. |
| RF15 | Navegación | Navegar entre módulos mediante un menú gráfico. |
| RF16 | Tablas | Utilizar `ttk.Treeview` para mostrar productos, clientes y pedidos. |
| RF17 | Formularios | Validar entradas antes de guardar información. |
| RF18 | Mensajes | Mostrar errores, confirmaciones y resultados con `messagebox`. |
| RF19 | Actualización | Refrescar las tablas después de cada operación. |
| RF20 | Persistencia | Guardar productos, clientes y pedidos en archivos JSON. |
| RF21 | Recuperación | Cargar automáticamente los datos guardados al iniciar la aplicación. |
| RF22 | Separación | Mantener las reglas de negocio independientes de las ventanas gráficas. |

## 5. Pantallas obligatorias

| Pantalla | Funcionalidades mínimas |
|---|---|
| Inicio | Menú principal y acceso a módulos. |
| Productos | Registrar, editar, eliminar y consultar productos. |
| Clientes | Registrar y consultar clientes. |
| Pedidos | Crear pedidos y agregar productos. |
| Detalle del pedido | Mostrar productos, cantidades, subtotales y total. |
| Pagos | Seleccionar medio de pago y procesar la transacción simulada. |
| Repartidores | Registrar, consultar y asignar repartidores disponibles. |
| Seguimiento | Consultar y actualizar estados de pedidos. |

## 6. Estados de los pedidos

Flujo principal:

```text
CREADO → PAGADO → EN_PREPARACION → EN_CAMINO → ENTREGADO
   └──────────────→ CANCELADO
```

La cancelación es una ruta alternativa, no una transición automática. El sistema debe validar cada cambio de estado y definir en qué estados se permite cancelar.

## 7. Reglas de negocio

1. No se pueden agregar al pedido cantidades superiores al stock disponible.
2. El stock nunca puede ser negativo.
3. Un pedido puede contener varios productos.
4. El sistema debe calcular automáticamente el subtotal, el despacho y el total.
5. Un pedido no puede pagarse dos veces.
6. Un pago rechazado no confirma la compra ni descuenta inventario.
7. Un repartidor no puede tener dos entregas simultáneas.
8. Cuando corresponda, la cancelación debe restituir el stock descontado, una sola vez.
9. Los pedidos entregados mantienen su estado final.
10. Las operaciones inválidas deben informar el error sin cerrar la aplicación.
11. El descuento de stock y la confirmación del pedido deben ejecutarse de forma consistente, evitando descuentos duplicados.
12. El sistema debe impedir transiciones de estado no permitidas.

## 8. Modelo de clases propuesto

| Clase | Responsabilidad |
|---|---|
| `Producto` | Clase abstracta con atributos y comportamientos comunes. |
| `Comida` | Especialización de `Producto`. |
| `Bebida` | Especialización de `Producto`. |
| `Cliente` | Datos del comprador. |
| `Pedido` | Productos, totales, cliente y estado de la compra. |
| `DetallePedido` | Producto, cantidad, precio y subtotal de cada línea. |
| `MetodoPago` | Abstracción de los mecanismos de pago. |
| `PagoTarjeta` | Implementación de pago con tarjeta. |
| `PagoEfectivo` | Implementación de pago en efectivo. |
| `PagoBilletera` | Implementación de pago con billetera digital. |
| `Repartidor` | Disponibilidad y asignación de entregas. |
| `FlashFood` | Coordinación de la operación general del sistema. |

El modelo puede ampliarse con servicios, controladores y repositorios cuando sea necesario para mantener responsabilidades claras.

## 9. Aplicación de Programación Orientada a Objetos

| Concepto | Aplicación requerida |
|---|---|
| Abstracción | Clases abstractas para productos y medios de pago, utilizando `abc`. |
| Encapsulamiento | Atributos protegidos mediante convenciones y propiedades o métodos que validen cambios. |
| Herencia | Especializaciones de productos y medios de pago. |
| Polimorfismo | Distintas implementaciones de una operación común de pago. |
| Composición | Un `Pedido` contiene múltiples `DetallePedido`. |

## 10. Arquitectura MVC

**Modelo:** clases de dominio, reglas de negocio, cálculos y servicios. No debe depender de Tkinter.

**Vista:** ventanas y componentes de Tkinter/ttk. Presenta datos y recibe interacciones, sin implementar las reglas de negocio.

**Controlador:** recibe eventos de la vista, coordina operaciones con el modelo y actualiza la interfaz.

**Persistencia:** repositorios o componentes dedicados a leer y escribir JSON, separados de las vistas.

Flujo de referencia:

```text
Vista (Tkinter + ttk)
         ↕
     Controlador
         ↕
   Modelo / Servicios
         ↕
  Repositorios JSON
```

## 11. Requerimientos no funcionales

- Organizar el código en módulos y clases con responsabilidades claras.
- Utilizar nombres descriptivos para clases, atributos y métodos.
- Separar interfaz, controladores, modelo y persistencia.
- Validar entradas, cantidades, precios, stock y cambios de estado.
- Manejar errores de archivos y datos inválidos sin cerrar inesperadamente la aplicación.
- Utilizar colecciones para administrar productos, clientes y pedidos.
- Permitir incorporar nuevos productos y medios de pago con cambios mínimos.
- Mantener una interfaz comprensible, con etiquetas claras y mensajes de retroalimentación.
- Evitar duplicar reglas de negocio en diferentes pantallas.

## 12. Desafíos adicionales

Estos desafíos amplían el caso y pueden abordarse después de los requerimientos obligatorios.

| Desafío | Regla |
|---|---|
| Hora punta | Aumentar el costo de despacho un 25%. |
| Cliente VIP | Aplicar un descuento del 10%. |
| Pago rechazado | No confirmar el pedido ni descontar inventario. |
| Cancelación | Restituir el stock cuando corresponda. |
| Lluvia | Definir e implementar una regla especial de despacho. |
| Nuevo medio de pago | Incorporar transferencia sin modificar las clases de pago existentes. |

## 13. Etapas de desarrollo sugeridas

1. **Modelado POO:** identificar clases, atributos, métodos, relaciones y reglas; construir el diagrama UML.
2. **Lógica de negocio:** implementar productos, clientes, pedidos, pagos, inventario y repartidores sin interfaz gráfica.
3. **Interfaz gráfica:** crear las pantallas con Tkinter y ttk.
4. **Integración MVC:** conectar eventos de la vista con controladores y servicios del modelo.
5. **Persistencia JSON:** guardar y recuperar información de forma consistente.
6. **Pruebas e integración:** verificar flujos correctos y casos de error.

## 14. Entregables

1. Código fuente ejecutable en Python.
2. Diagrama UML de clases.
3. Aplicación de escritorio con las pantallas obligatorias.
4. Archivos JSON de persistencia o datos de prueba.
5. Demostración del flujo completo: registro de productos, creación de pedido, pago, preparación, despacho y entrega.
6. Explicación de cómo se aplicaron los cuatro pilares de POO.
7. Evidencia de validaciones y manejo de errores.

## 15. Criterios de evaluación

| Criterio | Ponderación |
|---|---:|
| Aplicación de los cuatro pilares de POO | 30% |
| Implementación de reglas de negocio | 20% |
| Interfaz gráfica con Tkinter y ttk | 20% |
| Arquitectura MVC y organización del código | 15% |
| Persistencia JSON | 10% |
| Calidad del código y validaciones | 5% |
| **Total** | **100%** |

## 16. Organización del trabajo

Se propone trabajar en equipos de **3 a 4 estudiantes**. La duración original de referencia era de **dos clases de 90 minutos** para el núcleo del caso; la versión ampliada con interfaz gráfica, MVC y persistencia debe planificarse en más sesiones según el avance del curso.

---

**Resultado esperado:** una aplicación de escritorio funcional para FlashFood, construida en Python, que demuestre la aplicación práctica de POO, reglas de negocio, MVC, interfaces gráficas y persistencia de datos.
