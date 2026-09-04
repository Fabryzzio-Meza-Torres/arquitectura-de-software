# Requerimientos No Funcionales

## Arquitectura y conectividad

- **RNF-1:** La solución debe operar sobre una arquitectura de redes locales (LAN) por colegio, con un servidor departamental intermediario entre el nivel central (Lima) y la laptop-servidor de cada colegio.
- **RNF-2:** Los usuarios deben poder acceder a la plataforma desde la red LAN del colegio (en clase), sin requerir internet en cada laptop de salón.
- **RNF-3:** El sistema debe garantizar el envío de archivos pesados con reintento (retry) automático ante fallos de transferencia.
- **RNF-4:** El sistema debe manejar el procesamiento y sincronización de datos por lotes (batch) para tolerar pérdidas de conexión y mantener respaldos (backup) de la información.
- **RNF-5:** El sistema debe eliminar automáticamente los archivos al cierre de cada bimestre para liberar espacio de almacenamiento.

## Modularidad y experiencia de usuario

- **RNF-6:** El sistema debe estar organizado en módulos y componentes bien definidos y desacoplados.
- **RNF-7:** El desarrollo debe priorizar la experiencia de los usuarios finales.
- **RNF-8:** La interfaz del sistema debe ser intuitiva y fácil de usar para todos los perfiles de usuario.
