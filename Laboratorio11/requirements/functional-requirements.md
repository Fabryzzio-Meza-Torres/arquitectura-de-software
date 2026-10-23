Requerimientos Funcionales

- RF1: Gestión de envíos: El sistema permite a los estudiantes enviar código y archivos desde su aplicación móvil.
- RF2: Subida docente: El sistema permite a los profesores subir entregas y gestionar evaluaciones desde interfaces web o de escritorio.
- RF3: Enrutamiento inteligente: El enrutador redirige automáticamente las solicitudes hacia el sistema nuevo o hacia la laptop legacy según el curso.
- RF4: Segmentación de colas: El sistema organiza las entregas en colas separadas por tipo de curso (Programación, Arquitectura e IA).
- RF5: Calificación automática: El sistema procesa de forma asíncrona y aislada el código de los alumnos mediante workers especializados.
- RF6: Revisión manual: El sistema brinda a los profesores una herramienta para realizar revisiones y calificaciones manuales directas.
- RF7: Consulta de estados: El sistema permite a los usuarios consultar en tiempo real el estado y resultado de sus entregas.
- RF8: Notificaciones push: El sistema avisa automáticamente al celular del estudiante cuando su entrega ha sido calificada.
- RF9: Reintento por infraestructura: El sistema re-encola automáticamente aquellas tareas interrumpidas por fallas de la nube sin afectar al alumno.
- RF10: Manejo de errores críticos: El sistema desvía a una cola de mensajes muertos (DLQ) los fallos repetitivos para la revisión humana.
