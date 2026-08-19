# Persona: Mariel Carolina Tovar Tolentino


## Datos generales
- **Rol:** Jefa de Área - UCI
- **Edad / experiencia:** 45 años, 15 años de experiencia
- **Contexto de trabajo:** Trabaja en el Hospital Rebagliati (Jesús María, Lima) de día pero también hace guardias de supervisión. Está a cargo de los 3 turnos (mañana, tarde, noche) y como 20 personas entre médicos y enfermeros.


## Objetivos
<!-- ¿Qué quiere lograr esta persona al usar el sistema? -->
- Tener visibilidad total y en tiempo real del estado de cada cama UCI y del personal asignado a cada turno
- Garantizar que ningún cambio de turno quede sin el diagnóstico o historial clínico transferido correctamente
- Detectar falta de personal y cruces de horario antes de que se conviertan en un incidente
- Poder auditar después de una emergencia qué pasó y quién respondió


## Frustraciones / Dolores actuales
<!-- ¿Qué le duele hoy sin el sistema? Conecta con los 3 problemas críticos del caso -->
- No tiene manera de saber si el médico que se va dejó anotado el diagnóstico antes de que entre el otro turno
- Se entera de las emergencias de madrugada recién al día siguiente, cuando ya no puede hacer nada
- No hay forma de confirmar que una alerta le llegó a la persona correcta y que esta persona la vio
- Arma los horarios a mano (con Excel y llamadas) y se da cuenta de los cruces cuando ya causaron un problema

## Escenario de uso típico
<!-- Un día/turno típico de esta persona interactuando con el sistema -->

Claudia llega en la mañana y revisa un dashboard con el estado de las 24 horas anteriores: qué pacientes tuvieron cambio de turno, si el diagnóstico quedó completo, y si hubo alguna alerta nocturna sin atender a tiempo. Durante el día ajusta el cuadro de turnos de la semana siguiente, verificando que no haya cruces de disponibilidad entre médicos. Si el sistema detecta que un turno se quedó sin médico responsable de guardia, Claudia recibe una notificación para reasignar antes de que sea crítico.


## Necesidades frente al sistema
<!-- Lista concreta: qué tiene que poder hacer el sistema para que Pablo esté satisfecho -->
- Dashboard en tiempo real del estado de cambio entre turnos (completo / incompleto / pendiente)
- Sistema de programación de horarios que bloquee o alerte cruces de disponibilidad automáticamente
- Auditoría completa de las emergencias nocturnas: a quién se contactó, tiempo de respuesta, si es que fue necesario contactar a otro médico, etc.
- Reportes de disponibilidad de personal por turno y por especialidad
- Alertas escalables de tal forma que si el médico de turno no responde en cierto tiempo, que el sistema le notifique a ella directamente



## Nivel técnico
<!-- ¿Qué tan cómodo es con tecnología? Afecta requerimientos de UX/rendimiento -->


Nivel medio: Se maneja bien con dashboards, reportes y apps móviles de uso diario, pero no es técnica. El sistema necesita ser visual con colores y gráficos fáciles de entender, de tal forma que la UX priorice la lectura rápida.