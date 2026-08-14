## 4. Requisitos Funcionales

| ID | Requisito funcional |
|---|---|
| RF-01 | El sistema debe permitir registrar y consultar diagnósticos y datos clínicos mediante un flujo simplificado, garantizando su disponibilidad inmediata en un dashboard central para todo el equipo. |
| RF-02 | El sistema debe conservar un log inmutable de todos los cambios, diagnósticos y alertas (indicando responsable, hora y escalamiento), garantizando recuperar la información clínica de toda la red en < 5 minutos tras caída para asegurar la continuidad del diagnóstico ante la rotación. |
| RF-03 | El sistema debe garantizar que el diagnóstico del médico saliente esté completo y disponible en la pantalla del médico entrante antes y durante el cambio de turno, requiriendo su registro antes de finalizar el turno. |
| RF-04 | El sistema debe administrar horarios evitando cruces. Si detecta un turno sin cobertura, bloqueará cruces y notificará de inmediato a la jefatura para asegurar que el diagnóstico del paciente en rotación tenga un receptor asignado. |
| RF-05 | El sistema debe permitir registrar, aprobar y comunicar ausencias, reemplazos y cambios de turno. |
| RF-06 | El sistema debe detectar alteraciones críticas y emitir alertas push de manera simultánea e instantánea a todo el equipo de guardia, persistiendo local y centralizadamente para soportar una escala de 10M hospitales sin pérdida de datos en tiempo real. |
| RF-07 | Ante una emergencia nocturna, el sistema debe contactar rápidamente al médico encargado mediante notificaciones push prioritarias; si no responde en 2 minutos, debe activar un flujo de escalamiento automático contactando al personal de retén o jefatura. |
| RF-08 | El sistema debe controlar las acciones y la información disponible según el rol del usuario. |
