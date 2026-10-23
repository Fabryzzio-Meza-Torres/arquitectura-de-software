Requerimientos No Funcionales

- RNF1: Alta disponibilidad: El sistema responde de inmediato ante picos masivos de tráfico gracias al encolamiento asíncrono con SQS.
- RNF2: Tolerancia a fallos: El sistema recupera automáticamente las tareas afectadas si una instancia de nube se apaga repentinamente.
- RNF3: Optimización de costos: La infraestructura de cómputo utiliza exclusivamente instancias Spot económicas para cumplir con el presupuesto.
- RNF4: Escalabilidad automática: El sistema dimensiona el número de workers dinámicamente según la cantidad de entregas pendientes en las colas.
- RNF5: Rendimiento en lecturas: El sistema soporta consultas masivas de notas utilizando réplicas de lectura en la base de datos.
- RNF6: Baja latencia: El sistema ofrece consultas de estado ultrarrápidas en milisegundos apoyándose en una capa de caché Redis.
- RNF7: Aislamiento seguro: El sistema ejecuta el código no confiable de los alumnos en sandboxes estrictamente seguros y sin red.
- RNF8: Modularidad: El sistema está diseñado en componentes independientes para escalar y desplegarse por separado.
- RNF9: Durabilidad de datos: El sistema almacena con seguridad todo el código y los resultados en S3 para evitar pérdidas.
- RNF10: Observabilidad: El sistema monitorea constantemente métricas clave como el tamaño de las colas, el rendimiento y las interrupciones.
