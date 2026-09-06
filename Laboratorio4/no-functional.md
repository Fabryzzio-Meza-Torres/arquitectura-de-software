# Requerimientos No Funcionales

## Arquitectura y conectividad

- **RNF-1:** La solución debe operar sobre una arquitectura de redes locales (LAN) por colegio, con un servidor departamental intermediario entre el nivel central (Lima) y la laptop-servidor de cada colegio.
- **RNF-2:** Los usuarios deben poder acceder a la plataforma desde la red LAN del colegio (en clase), sin requerir internet estable en cada laptop de salón.
- **RNF-3:** El sistema debe soportar transferencia reanudable (resumable upload/download) para el envío de archivos pesados, mediante fragmentación en partes pequeñas (chunks), de modo que ante una interrupción de conectividad la transferencia continúe desde la última parte confirmada, sin reiniciar desde cero.
- **RNF-4:** El reintento debe ser automático, combinando: (a) detección del momento en que vuelve la conexión, (b) una revisión periódica programada como respaldo por si no se detecta el regreso de la conexión, y (c) la opción de que el usuario fuerce el reintento manualmente.
- **RNF-5:** Si dos mecanismos de reintento se activan al mismo tiempo sobre el mismo archivo, el sistema debe asegurar que solo uno esté procesándolo en ese momento, evitando el envío duplicado de una misma parte.
- **RNF-6:** El mecanismo de reintento descrito en RNF-3, RNF-4 y RNF-5 aplica a los envíos punto a punto (profesor→central, central→departamento, departamento→colegio individual). El envío masivo por multicast a todos los colegios de una región se maneja en modalidad best-effort: se transmite una vez durante la ventana definida, sin mecanismo de reparación o reenvío automático en caso de pérdida parcial.
- **RNF-7:** El sistema debe manejar el procesamiento y sincronización de datos por lotes (batch) para tolerar pérdidas de conexión y mantener respaldos (backup) de la información.
- **RNF-8:** El sistema debe eliminar automáticamente los archivos al cierre de cada bimestre para liberar espacio de almacenamiento.

## Modularidad y experiencia de usuario

- **RNF-9:** El sistema debe estar organizado en módulos y componentes bien definidos y desacoplados.
- **RNF-10:** El desarrollo debe priorizar la experiencia de los usuarios finales.
- **RNF-11:** La interfaz del sistema debe ser intuitiva y fácil de usar para todos los perfiles de usuario.
