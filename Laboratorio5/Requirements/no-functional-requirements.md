1. El sistema posee Guardrails frente a situaciones que sea peligroso actuar por cuenta propia,
   por lo que debe esperar confirmación del Área de ingeniería para proseguir
2. El sistema posee una base de conocimiento mediante RAG para la resolución de problemas de
   manera rápida. Este RAG es autoalimentado con cada interacción de cada incidente. En cada noche/madrugada se reentrenará con los tickets resueltos del día.
3. El sistema posee MCP a las bases de datos de la empresa para alimentar su conocimiento
4. Si el Harness no puede resolver el incidente, el ticket generado por el Área de soporte debe ser
   escalado al Área de ingeniería
5. El sistema posee MCP a Slack del Área de ingeniería para escalar los incidentes al Jefe del área
   correspondiente, el cual deriva los tickets a su equipo. (Idempotencia)
6. El sistema debe poder manejar 10,000 incidentes por semana o más, mediante un sistema de prioridad de tickets dandole peso a cada uno y manejandolo con un priority queue FIFO.
7. El usuario puede catalogar tickets como no resolved
8. El sistema se encarga de notificar el estado de un ticket a los involucrados.
9. El sistema debe ser capaz de ayudar a soluciona customer escalations en un 1 dia y engineering
   escalations de 3 días.
10. El sistema debe asignar un request limit para no saturar las sesiones de la LLM local.
