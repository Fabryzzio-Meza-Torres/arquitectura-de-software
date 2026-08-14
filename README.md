# Prueba-Test-Essalud

## 1. Definición del Problema

**¿Qué está lanzando Essalud y por qué?**

Essalud está lanzando un software para la gestión de su red de Unidades de Cuidados Intensivos (UCI) a nivel regional. La necesidad surge porque en estos ambientes existe una alta rotación de médicos internistas, lo que hace crítico garantizar que el diagnóstico y la información clínica del paciente estén siempre disponibles para el personal del siguiente turno.

**¿Cuál es el alcance geográfico inicial y la visión de crecimiento?**

El piloto inicia en la región de Lima y sus distritos, con proyección de expansión a nivel nacional si resulta exitoso.

**¿Cuáles son los 3 problemas críticos a resolver?**

1. **Problema de rotación de doctor:** la alta rotación de médicos internistas genera riesgo de pérdida de continuidad en la información clínica, provocando que el personal del turno entrante no cuente con datos críticos o actualizados del paciente.

2. **Problema de medianoche:** ante emergencias durante la madrugada, existen dificultades para localizar y contactar rápidamente al médico responsable, así como para activar un flujo alternativo si este no está disponible, aumentando el riesgo de tiempos de reacción lentos.

3. **Problema de actualizaciones en tiempo real:** el sistema debe comunicar información crítica, alertas y diagnósticos de forma simultánea e instantánea a todo el equipo de guardia, y a la vez garantizar que esa información quede persistida de forma confiable, incluso ante fallos parciales o pérdida de conectividad.

### Requerimientos de Escalamiento

- **Lanzamiento:** 1K hospitales
- **6 meses:** 100K hospitales
- **2 años:** 10M hospitales

### Metas de Rendimiento

- **Tiempo de inicio de aplicación:** < 1 segundo
- **Configuración de aplicación:** < 5 segundos
- **Disponibilidad del sistema:** 99.9%
- **Tiempo de recuperación en caso de caída:** < 5 minutos

---

## 2. Usuarios / Clientes del Sistema

**Cliente:** Essalud

**Usuarios directos:**

| Actor                                                              | Necesidad principal frente al sistema                                                                                       |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Jefe de Área UCI                                                   | Visibilidad global de horarios, cobertura de turnos y estado de los pacientes de su unidad                                  |
| Médicos por especialidad (Intensivista, Anestesiólogo, Cardiólogo) | Acceso inmediato al diagnóstico y evolución del paciente al iniciar turno; ser contactado con prioridad ante una emergencia |
| Internos                                                           | Registrar y consultar información clínica; recibir alertas y tareas pendientes del turno anterior                           |
| Personal de Enfermería (Jefe, Universitario, Técnico)              | Registrar indicaciones y evolución del paciente; generar y recibir alertas clínicas                                         |

**Usuarios indirectos:**

| Actor         | Necesidad principal frente al sistema                                                          |
| ------------- | ---------------------------------------------------------------------------------------------- |
| Pacientes UCI | Continuidad y calidad de la atención médica, aunque no interactúan directamente con el sistema |

---

## 3. Personas / Usuarios Modelo

<!-- Actualiza los enlaces cuando crees los archivos correspondientes en /Personas -->

- [Mariel Carolina Tovar Tolentino](./Personas/MarielCarolinaTovarTolentino.md) — Jefa de Área
- [Rensso Victor Hugo Mora Choque](./Personas/RenssoVictorHugoMoraChoque.md) — Médico Intensivista
- [Carlos Balbuena Palacios](./Personas/CarlosBalbuenaPalacios.md) — Enfermero
- [Shakira Carol G Frisancho](./Personas/ShakiraCarolGFrisancho.md) — Interna

---
