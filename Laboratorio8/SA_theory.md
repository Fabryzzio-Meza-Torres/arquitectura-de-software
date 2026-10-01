# Plantilla para examen parcial

## Reliability & Availability

Reliability consiste en asegurar que la experiencia del usuario no se vea afectada y en proteger los recursos limitados del sistema. Para medir el desempeño del sistema se utilizan fórmulas estándar basadas en códigos de estado HTTP.

### Métricas de disponibilidad y confiabilidad

- **Availability (server-side only):** Mide la disponibilidad de la infraestructura, omitiendo fallas originadas por el cliente.

  **Availability:** `2xx / (2xx + 5xx)`

- **Reliability (client- and server-side):** Mide la probabilidad de éxito global considerando tanto errores del cliente (`4xx`) como fallas del servidor (`5xx`).

  **Reliability:** `2xx / (2xx + 4xx + 5xx)`

### Analítica de latencia mediante percentiles

- **¿Por qué evitar el promedio?** El promedio distorsiona la métrica de rendimiento al ocultar valores extremos (_outliers_).
- **Percentiles (P50, P90, P95 y P99):** Indican el tiempo de respuesta de distintos grupos de solicitudes.
- **P95 y P99:** Indican que el 95% o 99% de las solicitudes responden en un tiempo menor o igual al valor del percentil.
- **Experiencia base:** Los percentiles P95 y P99 representan el punto base de la experiencia del usuario y corresponden frecuentemente a casos de uso pesados pero altamente valiosos, como carritos de compra con más de 40 ítems.

### Health endpoints

Cada servidor debe exponer endpoints de salud para revisar su disponibilidad y rendimiento, y detectar si está sobrecargado.

### Load balancer

Distribuye las solicitudes entrantes entre varios servidores para evitar la sobrecarga y mejorar la disponibilidad y el rendimiento.

**Caso de uso:** Una tienda online reparte miles de solicitudes entre tres servidores web para que ninguno se sature durante una campaña de ofertas.

#### Algoritmos de balanceo

1. **Round Robin:** Distribuye las solicitudes secuencialmente, en orden de llegada, entre los servidores disponibles. Requiere que los servidores tengan hardware e infraestructura idéntica.
2. **Weighted Round Robin:** Asigna un peso (_weight_) a cada servidor según su capacidad, enviando un mayor volumen de carga a los servidores de mayor potencia.
3. **Least Connection:** Dirige cada nueva solicitud al servidor que tenga el menor número de conexiones activas en ese instante.
4. **Weighted Least Connection:** Envía cada nueva solicitud al servidor con menos conexiones activas, considerando la ponderación de capacidad asignada a cada uno.

#### Weighted least connection load balancer

Envía cada nueva solicitud al servidor con menos conexiones activas, considerando que algunos servidores tienen mayor capacidad que otros.

**Caso de uso:** Un servidor potente con peso 3 puede recibir más conexiones que otro con peso 1, pero se evita enviar tráfico al servidor que ya está más saturado.

### Circuit breaker

Detiene temporalmente las llamadas a un servicio que está fallando para evitar que el problema se propague y darle tiempo de recuperarse.

**Caso de uso:** Si el servicio de pagos empieza a fallar repetidamente, el sistema deja de llamarlo durante unos segundos y responde con una alternativa o un error controlado.

### In-memory cache

Guarda datos temporalmente en la memoria RAM de una sola instancia para acceder a ellos mucho más rápido que desde la base de datos.

**Caso de uso:** Una API guarda en memoria la configuración de la aplicación, que se consulta constantemente y cambia muy poco.

### Distributed cache

Guarda datos temporales en un sistema compartido accesible para varias instancias o servidores, como Redis.

**Caso de uso:** Varias instancias de una tienda online comparten las sesiones de usuario en Redis para que cualquier servidor pueda atender al mismo usuario.

### Bulkhead pattern

Aísla recursos o componentes del sistema para que la falla o saturación de uno no afecte a los demás.

**Caso de uso:** Si un usuario con bots supera cierto nivel de solicitudes, sus conexiones se atienden desde un pool separado para que no consuma las conexiones reservadas para usuarios normales.

### Rate limiter

Limita cuántas solicitudes puede hacer un usuario o cliente en un periodo de tiempo para evitar abusos o la saturación del sistema.

**Caso de uso:** Una API permite un máximo de 100 solicitudes por minuto por usuario y bloquea temporalmente las solicitudes adicionales.

### Retry pattern

Reintenta automáticamente una operación que falló por un problema temporal.

**Caso de uso:** Si una llamada al servicio de pagos falla por timeout, el sistema la reintenta hasta tres veces antes de devolver un error.

#### Consideraciones del retry pattern

- **Costo computacional:** Reintentar `N` veces multiplica por `N` el consumo de recursos de CPU y memoria RAM.
- **Flujos síncronos:** El cliente permanece bloqueado. El número de reintentos depende del porcentaje histórico de éxito del servicio invocado.
- **Flujos asíncronos:** El reintento se gestiona mediante colas de eventos (SQS, RabbitMQ o Kafka), aplicando un tiempo de espera exponencial (_exponential backoff_). Tras agotar los intentos, el mensaje pasa a una _dead-letter queue_ (DLQ) para auditoría.

### Critical path

Es la secuencia de componentes u operaciones que necesariamente debe completarse para que una solicitud termine correctamente. Por eso, determina gran parte de la latencia total.

**Caso de uso:** En una compra online, validar stock, procesar el pago y confirmar el pedido forman el critical path porque, si cualquiera falla o se demora, la compra no puede completarse.

### Event queue

Almacena eventos temporalmente en una cola para que otros servicios los procesen de forma asíncrona, normalmente siguiendo un orden FIFO.

**Caso de uso:** Si llegan miles de compras al mismo tiempo, los eventos `PedidoCreado` se guardan en la cola para que servicios como email o facturación los procesen gradualmente sin saturar el sistema.

### Resultado síncrono

El cliente llama al servicio y se queda bloqueado esperando la respuesta, ya sea de éxito o de error, antes de continuar.

**Ejemplo:** `Payment Service` llama a `Bank API` y no puede continuar hasta saber si el pago fue aprobado.

### Throttling

Son las políticas del sistema para limitar el número de llamadas que puede hacer un usuario, sistema o cliente. El rate limiter suele aplicarse a nivel de API, mientras que el throttling puede aplicarse de forma más atómica a usuarios o sistemas de terceros.

### Resultado asíncrono

El cliente no espera la respuesta: deja el trabajo pendiente y continúa.

**Ejemplo:** Tras un pago exitoso, `Receipt Service` debe enviar el comprobante y `Revenue Service` debe registrar el ingreso del desarrollador. Como nadie está esperando en pantalla, si una operación falla, el reintento se coloca como mensaje en una cola de eventos (SQS, RabbitMQ o Kafka) y un worker lo procesa después, con espera creciente entre intentos (backoff). Si los reintentos se agotan, el mensaje pasa a una dead-letter queue para su revisión.

### Fitness functions

Son métricas o pruebas automáticas que verifican continuamente que la arquitectura siga cumpliendo ciertas restricciones de calidad.

**Caso de uso:** Un test detiene el despliegue si la latencia de una API supera 200 ms o si un servicio rompe una regla de dependencia.

### SPOF (single point of failure)

Es un componente único cuya falla puede provocar que todo el sistema deje de funcionar.

**Caso de uso:** Si toda la aplicación depende de una sola base de datos y esta cae, ningún usuario puede utilizar el sistema.

### Sticky sessions

Hace que las solicitudes de un mismo usuario sean dirigidas siempre al mismo servidor durante su sesión.

**Caso de uso:** Si el usuario inicia sesión en el servidor A y su carrito está guardado localmente allí, sus siguientes solicitudes siguen llegando al servidor A.

### Distributed caching

Guarda datos temporales en una caché compartida que puede ser utilizada por múltiples servidores o instancias.

**Caso de uso:** Varias instancias de una aplicación consultan Redis para obtener la sesión o el carrito del usuario sin acceder constantemente a la base de datos.

### Modularity

Divide el sistema en módulos independientes, cada uno responsable de una parte específica de la aplicación.

**Caso de uso:** Separar una tienda online en módulos de pagos, usuarios, productos y pedidos permite modificar uno sin rehacer todo el sistema.

### Cohesion

Mide qué tan relacionadas están las responsabilidades dentro de un mismo módulo. Una cohesión alta significa que el módulo se enfoca en una sola función.

**Caso de uso:** Un módulo `PaymentService` que solo contiene lógica relacionada con pagos tiene alta cohesión.

### Coupling

Mide cuánto depende un módulo de otros. Un bajo acoplamiento facilita modificar componentes sin afectar al resto.

**Caso de uso:** Si `OrdersService` depende directamente de muchos detalles internos de `PaymentService`, un cambio en pagos podría romper los pedidos.

### Bottleneck

Es un componente cuya capacidad limita el rendimiento de todo el sistema porque recibe más carga de la que puede procesar.

**Caso de uso:** Si diez servidores web dependen de una única base de datos lenta, la base de datos se convierte en el bottleneck.

### Instability

Mide qué tan propenso es un módulo a cambiar debido a sus dependencias. Cuanto más depende de otros componentes, más inestable es.

**Caso de uso:** Un módulo que depende de cinco servicios externos tendrá mayor instability porque los cambios en cualquiera de ellos pueden obligarlo a cambiar.

### Util classes

Son clases que agrupan funciones reutilizables y generales que no pertenecen a una entidad específica, normalmente mediante métodos estáticos.

**Caso de uso:** Una clase `DateUtils` puede contener funciones para convertir, validar y formatear fechas utilizadas en distintas partes del sistema.

## Ejemplos de requerimientos funcionales

- **RF1:** El sistema debe distribuir contenido mediante una red de servidores optimizados (CDN o edge servers) en LATAM para reducir la latencia y mejorar la velocidad de descarga.
- **RF2:** El sistema debe permitir la reanudación de descargas interrumpidas para evitar la pérdida de progreso por cortes de conexión.
- **RF4:** El sistema debe soportar múltiples monedas locales, como soles, pesos mexicanos, reales y pesos argentinos.
- **RF5:** El sistema debe integrar medios de pago regionales, como PIX, Mercado Pago, Yape, OXXO y PagoEfectivo.
- **RF6:** El sistema debe mostrar los precios directamente en la moneda local del usuario para evitar confusiones por el tipo de cambio.
- **RF7:** El sistema debe estar disponible en español neutro, portugués brasileño e inglés.
- **RF12:** El sistema debe integrar un orquestador de pagos que unifique los distintos métodos locales bajo una única pasarela.

## Ejemplos de requerimientos no funcionales

### Rendimiento y disponibilidad

- **RNF1:** El sistema debe garantizar una disponibilidad mínima del 99.9% anual para el servicio de descargas y compras.
- **RNF2:** El tiempo de respuesta de la plataforma web no debe superar los 2 segundos en el 95% de las solicitudes.
- **RNF3:** El sistema debe permitir descargas concurrentes de al menos 1 millón de usuarios distribuidos en LATAM sin degradar la experiencia.
- **RNF4:** La CDN o infraestructura de distribución debe soportar picos de tráfico en lanzamientos masivos de hasta 5 veces el tráfico promedio.

### Escalabilidad

- **RNF5:** El sistema debe poder escalar horizontalmente, incorporando nuevos servidores o regiones sin interrumpir el servicio.
- **RNF6:** El sistema debe soportar la integración de nuevos métodos de pago sin afectar los existentes.
- **RNF7:** El sistema debe permitir agregar nuevos idiomas y monedas en el futuro con cambios mínimos en la arquitectura.

### Usabilidad y accesibilidad

- **RNF8:** La interfaz debe ser responsiva y usable desde navegadores web, clientes de escritorio y dispositivos móviles.
- **RNF9:** La plataforma debe ofrecer localización de la interfaz con detección automática del idioma según la región del usuario.

## Ejemplos de fitness functions

### Rendimiento y disponibilidad

- **FF1 (tiempo de respuesta web):** El 95% de las solicitudes HTTP debe responder en ≤ 2 segundos, medido con APM o monitoring.
- **FF2 (descargas concurrentes):** El sistema debe sostener ≥ 1 millón de descargas simultáneas con un throughput mínimo de 10 MB/s por usuario en condiciones de prueba de carga.
- **FF3 (disponibilidad):** El sistema debe mantener un uptime ≥ 99.9% mensual para los servicios críticos de compras y descargas.

### Escalabilidad

- **FF4 (autoescalado de infraestructura):** Ante un aumento del 300% en el tráfico, el sistema debe autoescalar instancias en < 5 minutos y mantener los tiempos de respuesta dentro de lo esperado.
- **FF5 (integración de pagos):** La adición de un nuevo método de pago no debe aumentar el tiempo de checkout en más de 5%.
- **FF6 (extensibilidad):** La inclusión de una nueva moneda o idioma debe requerir ≤ 2 días de desarrollo y despliegue.

### Usabilidad y accesibilidad

- **FF7 (compatibilidad multidispositivo):** El sistema debe renderizar correctamente en ≥ 95% de los navegadores y dispositivos probados mediante tests automatizados.
- **FF8 (accesibilidad):** Los tests automáticos de accesibilidad deben cumplir ≥ 90% de conformidad con WCAG 2.1 AA.
- **FF9 (localización):** El idioma detectado automáticamente debe coincidir con la configuración del usuario en ≥ 95% de las pruebas.

---

## Conceptos complementarios de arquitectura de software

### 1. Métricas formales de rendimiento y disponibilidad

#### Fórmulas de disponibilidad y confiabilidad (HTTP status codes)

- **Availability (server-side only):** Mide la capacidad del servidor para estar operativo, excluyendo errores atribuidos al cliente.

  $$
  \text{Availability} = \frac{2xx}{2xx + 5xx}
  $$

- **Reliability (client- and server-side):** Mide la probabilidad de éxito global considerando fallas del cliente, como peticiones mal formadas (`4xx`), y del servidor (`5xx`).

  $$
  \text{Reliability} = \frac{2xx}{2xx + 4xx + 5xx}
  $$

#### Analítica de latencia por percentiles (P50, P90, P95 y P99)

- **¿Por qué no usar el promedio?** El promedio oculta los picos de latencia (_outliers_) y distorsiona la métrica real de calidad de servicio.
- **P95 y P99:** Indican el tiempo máximo en el que se procesa el 95% o 99% de las solicitudes.
- **Experiencia base:** Los percentiles altos (P95 y P99) representan el nivel base de experiencia del usuario y suelen corresponder a los casos de uso más complejos y valiosos del sistema, como carritos de compra masivos con muchos ítems.

#### Definición real de carga (load)

La carga no se mide únicamente por la cantidad de usuarios conectados, sino por las unidades reales de datos o transacciones procesadas por unidad de tiempo: RPS, throughput o volumen de registros procesados.

### 2. Metodología de diseño de sistemas (pasos EDALS)

Es un marco de trabajo estructurado para diseñar arquitecturas partiendo de requerimientos ambiguos:

1. **E - Estimación de capacidad**
   - **Entradas:** Usuarios totales, usuarios activos, solicitudes por segundo (RPS), logins por segundo y almacenamiento estimado.
   - **Cálculos obligatorios:**
     - **Servidores requeridos:** Basado en la capacidad de cómputo por instancia.
     - **Almacenamiento requerido:** Volumen total de datos acumulados en el tiempo.
     - **Ancho de banda (bandwidth):** Velocidades requeridas de entrada (_upload speed_) y salida (_download speed_).

2. **D - Diseñar el servicio**
   - Selección del patrón de alto nivel: monolito, 3-Tier o microservicios.
   - Elección del motor de persistencia: SQL o NoSQL.
   - Diseño del API contract: endpoints HTTP/REST y contratos de mensajes.

3. **A - Articular el modelo de datos**
   - Definición del esquema de base de datos, relaciones entre entidades y estrategias de indexación.

4. **L - Listar componentes**
   - Diagramación de la arquitectura base conectando los bloques esenciales (_building blocks_): CDN, API Gateway, load balancers, servidores de aplicación, caché distribuida (Redis), base de datos principal y réplicas, colas de mensajes y motores de búsqueda (Elasticsearch).

5. **S - Scale (escalar la arquitectura)**
   - Estrategia de crecimiento progresivo según el volumen de usuarios:
     - **< 1,000 usuarios:** Servidor único de aplicación y base de datos integrada.
     - **1k - 10k usuarios:** Separación de capas con load balancer y réplicas de lectura en la base de datos.
     - **100k usuarios:** Introducción de una capa de caché (Redis) e infraestructura multirregión.
     - **500k usuarios:** Integración de CDN para contenido estático y activos pesados.
     - **1M+ usuarios:** Fragmentación de la base de datos (_sharding_) y desacoplamiento asíncrono con workers y colas.

### 3. Estrategias de migración y tolerancia a fallos

#### Patrón Strangler Fig (Strangler Router)

Permite migrar gradualmente un sistema heredado (_legacy_) hacia una nueva arquitectura, como microservicios, interceptando las peticiones en un router y redirigiendo el tráfico progresivamente a los nuevos componentes hasta retirar el monolito por completo.

#### Tácticas de tolerancia a fallos

- **Degradación elegante (graceful degradation):** Capacidad del sistema de continuar operando con funcionalidad limitada o alternativa, en lugar de sufrir un colapso total cuando fallan componentes secundarios.
- **Chaos engineering:** Práctica de inyectar fallas de forma controlada en producción o en entornos de prueba para verificar la resiliencia real de la arquitectura.
- **Diferencia entre arquitectura y diseño:**
  - **Arquitectura:** Define el **qué** y el **dónde**: estructuras de alto nivel, límites de componentes e interacciones.
  - **Diseño:** Define el **cómo**: implementación interna de módulos, patrones de código y clases.
- **Top-down design:** Enfoque metodológico donde el análisis parte de las abstracciones de alto nivel de la arquitectura hacia el detalle específico de cada componente.
