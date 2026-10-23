Universidad de Ingenieria y Tecnologia
Departamento de Ciencias de la Computación

Arquitectura de Software

Caso de Estudio #11
2026 - II

Keywords:
Top-Down design
Fitness functions
Pipeline
Reliability
Caching
Scalability
Availability

Caso de Estudio: Spotty( hard - new!)

Actualmente en la universidad UTC se tiene que únicamente el curso de arquitectura de software se ha implementado en un servidor local(una laptop!) un sandbox por alumno corregir los entregables de código de sus alumnos. Para ello usan workers(minions) que corrigen la prueba(código, diagramas). Dado el éxito de este sistema de calificación se quiere expandir al resto de cursos.
Por lo que tenemos:

- Cursos de Programación - Pruebas unitarias/Codigo - P99 = 1 minuto
- Cursos de Arquitectura - Diagramas/Código - P99 = 10 minutos
- Cursos de IA - Modelos, Ejecuciones con GPU - P99 = 40 minutos a más

  (\_) Considerar tambien el uso de memoria.
  El área de TI evaluó el budget y solo aprobó el uso de instancias Spot de AWS para los sandboxes/workers, porque cuestan mucho menos que las on-demand. Pero AWS puede reclamarlas con 2 minutos de aviso o quedarse sin capacidad Spot del tipo que usted pidió, y las de GPU son las más escasas.
  Usted y su equipo han sido elegidos para diseñar la arquitectura que soporte este requerimiento. Recordar que los profesores acceden desde una desktop pero los estudiantes podrán acceder desde una app mobile para ver el estado de sus entregables. También se tiene que hay cursos que son muy demandados y que tienen mayor cantidad de alumnos.Los profesores tienen como máximo 2 días para entregar las notas de sus alumnos.

  (\_) Cada ejecución corre “código” no confiable de un alumno dentro de un sandbox.

  (**) Cada curso tiene su propia imagen base de 3 a 5 GB.
  (\***) El uso no es constante: casi todas las entregas llegan en los últimos 30 minutos antes de la fecha límite.
  (\*\*\*\*) Algunos alumnos entregan código que pueden subir la memoria o ser ineficientes.
