# Guía docente de FlashFood

## Objetivo

Modelar un proceso de negocio usando clases, encapsulación, abstracción, herencia, polimorfismo y composición; verificar sus reglas antes de conectar una interfaz gráfica.

## Secuencia sugerida: seis sesiones de 90 minutos

1. **Análisis del negocio:** identificar cliente, producto, pedido, pago y repartidor. Redactar reglas y recorrer estados. Ejecutar `flashfood`.
2. **Objetos y composición:** crear clientes y productos; calcular subtotales y total. Distinguir atributo de instancia y propiedad calculada. Estudiar dataclasses y validaciones.
3. **Encapsulación y estados:** intentar entregar un pedido sin pago; explicar la excepción. Comparar modificar un atributo con llamar a una operación de negocio.
4. **Abstracción, herencia y polimorfismo:** comparar personas y medios de pago. Crear `PagoTransferenciaSimulada` sin cambiar `Pedido.pagar()`. Probar aprobación y rechazo.
5. **Capas y pruebas:** inspeccionar `ServicioPedidos`, sustituir el repositorio y ejecutar unittest. Explicar por qué los imports de Qt no aparecen en el dominio.
6. **Escritorio y eventos:** instalar el extra desktop, recorrer la ventana y conectar un formulario de cliente a `servicio.recibir()`. La vista muestra errores; el dominio decide qué se permite.

## Ejercicio guiado

Implementar un nuevo medio de pago que acepte un indicador de aprobación, devuelva `ResultadoPago` y valide montos. Crear una prueba que pague usando ese objeto. La prueba debe demostrar que el pedido permanece recibido si el pago falla y pasa a pagado si tiene éxito, sin modificar `Pedido`.

## Ejercicios de extensión

- Añadir costo de despacho, decidir quién lo calcula y verificar el total.
- Implementar un catálogo y formulario de cantidades; no duplicar reglas en la vista.
- Crear un repositorio SQLite con reconstrucción de pedidos e historial. Diseñar primero cómo rehidratar el agregado sin saltarse validaciones.
- Añadir cancelación y reembolso: definir transiciones y contratos antes de escribir código.
- Añadir historial con fecha UTC y actor de cada transición.
- Implementar una lista de pedidos con selección por identificador.
- Identificar la condición de carrera de la asignación en memoria y proponer una solución transaccional.

## Evaluación sugerida

| Criterio | Ponderación |
| --- | --- |
| Reglas e invariantes del pedido | 30% |
| Aplicación y explicación de los fundamentos POO | 25% |
| Separación de dominio, aplicación e interfaz | 20% |
| Pruebas de éxito y de operaciones inválidas | 15% |
| Documentación, commits y demostración | 10% |

Preguntas: ¿por qué no existe un setter de estado? ¿Qué cambia al añadir un pago nuevo? ¿Por qué usar composición para ítems? ¿Qué garantiza y qué no garantiza una clase congelada? ¿Dónde debe vivir una regla si la misma operación se usa desde consola y escritorio?

## Transición a una aplicación real

La ventana inicial evita mezclar aprendizaje de POO con un formulario complejo. Posteriormente agregar un controlador o presentador si crece la coordinación de vistas. Las operaciones de red irían en trabajadores Qt y volverían al hilo de interfaz mediante señales. Nunca bloquear el hilo principal con llamadas remotas. Antes de operar dinero real, incorporar idempotencia de pagos, transacciones, manejo de errores de proveedor y auditoría.
