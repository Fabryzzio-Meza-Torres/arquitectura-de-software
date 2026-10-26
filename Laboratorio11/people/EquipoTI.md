# Equipo de TI - Infraestructura y seguridad

## Quién es

Área de TI de la universidad. Aprobó el presupuesto solo para instancias Spot de AWS en sandboxes y workers, y recibe las alertas del sistema. Responde por el costo de la infraestructura, la disponibilidad de la plataforma y la revisión manual de las entregas sospechosas.

## Necesidades del sistema

1. Que el cómputo de ejecución use exclusivamente instancias Spot y que el Autoscaler respete carga, prioridad y SLA.
2. Que el sistema resista el reclamo con 2 minutos de aviso y la falta de capacidad Spot, sobre todo en GPU, que es la más escasa.
3. Que el código no confiable de los alumnos corra aislado y sin acceso a credenciales, y revisar manualmente las entregas sospechosas antes de rechazarlas o liberarlas.
4. Monitorear el backlog, los reintentos, las interrupciones Spot y el uso de CPU y GPU, y recibir alertas.
5. Que ningún curso monopolice la capacidad ni quede sin atención.
6. Migrar los cursos del servidor local (la laptop) al sistema nuevo de forma gradual, con copia en sombra y verificación de paridad.

## Riesgos y éxito observable

Le preocupan el sobrecosto por instancias que no son Spot, el código malicioso o ineficiente que sature un nodo, y una migración que deje a un curso sin servicio. Puede seguir la migración curso por curso y recibir alertas antes de que se incumplan las 48 horas, y todo el cómputo de ejecución corre en Spot.
