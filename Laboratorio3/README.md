## Lab 3: SendIT system

Este laboratorio documenta, de arriba hacia abajo, la arquitectura y la especificación del
sistema de remesas internacionales SendIT. El contenido se organiza para mantener la
trazabilidad desde el caso de estudio hasta los requisitos, el diseño y sus evaluaciones.

### Estructura

| Carpeta                          | Contenido                                                                                                                                                         |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`study-case/`](study-case/)     | Caso de estudio que delimita el problema, propósito y entregables del laboratorio.                                                                                |
| [`people/`](people/)             | Personas involucradas: Sender, Receiver y AgencyWorker; incluye sus objetivos, necesidades y flujos principales.                                                  |
| [`core/`](core/)                 | Definición del producto: resumen, problema, objetivo, alcance, conceptos, necesidades, decisiones, experiencia esperada, flujos, fases y criterios de aceptación. |
| [`requirements/`](requirements/) | Backlog de requisitos funcionales y no funcionales de SendIT.                                                                                                     |
| [`design/`](design/)             | Artefactos de diseño técnico, como la definición de endpoints.                                                                                                    |
| [`agents/`](agents/)             | Especificación del agente evaluador (`eval-spec.md`) usada para auditar los requisitos.                                                                           |
| [`reports/`](reports/)           | Reportes históricos de cada iteración de la evaluación de especificaciones.                                                                                       |

### Orden de lectura sugerido

1. Revisar [`study-case/`](study-case/) para entender el encargo.
2. Consultar [`people/`](people/) y luego [`core/`](core/) para conocer los usuarios, las decisiones y los flujos.
3. Revisar [`requirements/`](requirements/) y [`design/`](design/) para ver la solución especificada.
4. Consultar [`agents/`](agents/) y [`reports/`](reports/) para conocer el método y los resultados de la evaluación.

La arquitectura Top-Down con el framework REDALE se encuentra en el siguiente Excalidraw: [https://excalidraw.com/#room=acbeb8c15396c59e3480,630MBf6fSVwPnXH-YW8gmg](https://excalidraw.com/#room=acbeb8c15396c59e3480,630MBf6fSVwPnXH-YW8gmg)

o si el link no funciona, también está una version en [top-down-REDALE.excalidraw](design/top-down-REDALE.excalidraw) dentro de la carpeta [`design/`](design/).

La evaluación de los specs está en [reports/report-iteration-3.md](reports/report-iteration-3.md)
