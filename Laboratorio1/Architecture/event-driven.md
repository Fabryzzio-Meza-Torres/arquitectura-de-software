# Arquitectura Event-Driven — Essalud UCI

## 1. Justificación

El sistema requiere notificar a médicos en tiempo real ante emergencias UCI, simultáneamente en todos los hospitales del Perú, sin caídas. La naturaleza del dominio —alertas clínicas críticas que no toleran pérdida ni latencia elevada— exige una arquitectura event-driven con tolerancia a fallos, persistencia garantizada y escalabilidad horizontal masiva (1K → 10M hospitales).

---

## 2. Topología de Colas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PRODUCIDORES (Hospitales)                           │
│  Hospital A ──► Event Gateway ──┐                                          │
│  Hospital B ──► Event Gateway ──┤                                          │
│  Hospital C ──► Event Gateway ──┼──► COLA GLOBAL (urgencias-general)       │
│  Hospital N ──► Event Gateway ──┘         │                                 │
│                                          ▼                                 │
│                              ┌───────────────────┐                         │
│                              │  Event Router     │                         │
│                              │  (fan-out)        │                         │
│                              └───────┬───────────┘                         │
│                                      │                                     │
│                    ┌─────────────────┼─────────────────┐                   │
│                    ▼                 ▼                  ▼                   │
│          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│          │ Cola Regional│  │ Cola Regional│  │ Cola Regional│             │
│          │ LIMA-CENTRO  │  │ LIMA-NORTE   │  │ PROVINCIAS   │             │
│          └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│                 │                  │                  │                     │
│          ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐             │
│          │Partición/CG  │  │Partición/CG  │  │Partición/CG  │             │
│          │ HOSP-AAA     │  │ HOSP-BBB     │  │ HOSP-CCC     │             │
│          └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│                 ▼                  ▼                  ▼                     │
│          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│          │  Consumidores│  │  Consumidores│  │  Consumidores│             │
│          │  (médicos)   │  │  (médicos)   │  │  (médicos)   │             │
│          └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Cola Global — `urgencias-general`

- **Propósito:** Recibe TODOS los eventos de diagnóstico y alerta de UCI de todos los hospitales del país.
- **Tolerancia a fallos:** Replicación factor ≥ 3 en al menos 3 zonas de disponibilidad.
- **Retención:** 7 días con retención extendida a 30 días en almacenamiento frío (S3/GCS).
- **Particionado:** Por hash del `hospital_id` para distribuir carga equitativamente.
- **Garantía:** At-least-once con deduplicación idempotente en receptor.

### 2.2 Colas Regionales — `urgencias-{region}`

- **Propósito:** Filtran eventos por región geográfica (LIMA-CENTRO, LIMA-NORTE, PROVINCIAS, etc.).
- **Alcance:** Cada región opera como consumer group independiente de la cola global.
- **Retención:** 24 horas (suficiente para reconexión de hospitales caídos).
- **Escalabilidad:** Se crean nuevas regiones conforme el sistema crece.

### 2.3 Entrega Hospitalaria — partición, no topic-por-hospital

**Un topic Kafka por hospital no escala a 10M hospitales.** Un cluster Kafka real soporta en la práctica un máximo de decenas de miles de particiones (~200K en clusters grandes bien tuneados); crear 10M topics/colas colapsa el broker mucho antes de llegar a esa escala. La topología correcta:

- **FASE 1-2 (≤100K hospitales):** un topic por región (`urgencias-{region}-p{0,1,2}`), **particionado por `hospital_id`**. Cada hospital consume su propia partición (o subconjunto) vía consumer group filtrado, sin necesitar un topic dedicado.
- **FASE 3 (10M hospitales):** partición jerárquica por `region` + `distrito` (hash de `hospital_id` dentro del distrito). El "aislamiento por hospital" se logra a nivel de **consumer group + ACL**, no de topic físico.
- **TTL:** 5 minutos para eventos de baja prioridad; sin TTL para alta prioridad.
- **Dead Letter Queue (DLQ):** por región (`urgencias-{region}-dlq`), evento marcado con `hospital_id` original. Reintentos:
  - **P0:** reintento inmediato (sin esperar el ciclo de reconciliación) + disparo simultáneo del flujo de escalamiento (3.1) por canal secundario — un P0 en DLQ no puede esperar 30s cuando su SLA es <2s.
  - **P1/P2:** worker de reconciliación cada 30 segundos, reintenta o escala al equipo de soporte tras 3 intentos.

---

## 3. Priority Queue — Clasificación de Severidad

Los eventos se clasifican en 3 niveles de prioridad, mapeados a **colas separadas por nivel** dentro de cada scope (global, regional, hospitalario):

| Prioridad | Nivel   | Tiempo Máx. Entrega | Ejemplo                                      |
| --------- | ------- | ------------------- | -------------------------------------------- |
| P0        | CRÍTICO | < 2 segundos        | Paro cardiorrespiratorio, fallo multiorgánico |
| P1        | ALTO    | < 10 segundos       | Deterioro respiratorio agudo, sepsis          |
| P2        | NORMAL  | < 60 segundos       | Cambio de turno, actualización de diagnóstico |

**Mecanismo de implementación:**

Cada scope tiene 3 sub-colas:
- `urgencias-general-p0` (CRÍTICO)
- `urgencias-general-p1` (ALTO)
- `urgencias-general-p2` (NORMAL)

El **Event Router** consume de las 3 sub-colas con **weighted fair queuing (peso 10:3:1)**: por cada 10 mensajes P0 procesados se garantiza turno a 3 P1 y 1 P2. P0 nunca espera detrás de P1/P2, pero P1/P2 **nunca se bloquean indefinidamente** — un pico masivo de P0 (desastre natural, sección 6.4) no debe dejar sin diagnósticos de rutina al resto del sistema por horas.

**Anti-priority-inversion:** Un worker exclusivo de P0 opera con recursos dedicados (CPU/memory guarantees) para que el colapso de P2 no afecte la entrega de P0.

---

## 3.1 Acknowledgement y Escalamiento (Problema de Medianoche)

Notificar no es suficiente: si el médico responsable no reacciona, el sistema debe activar un flujo alternativo automáticamente. Sin esto, una alerta P0 entregada con éxito a una cola puede quedar sin que ningún humano la vea.

**Flujo de ACK:**

1. Al entregarse un evento P0/P1 a un consumidor, éste debe emitir un **ACK explícito** (no basta el ACK de infraestructura del broker) dentro de una ventana de tiempo:
   - P0: 30 segundos.
   - P1: 2 minutos.
2. Si no hay ACK dentro de la ventana, el **Escalation Worker**:
   - Reenvía la alerta al **médico de respaldo** (`on_call_backup_id`, definido en el roster de turno).
   - Si tampoco hay ACK en la misma ventana, escala al **Jefe de Área UCI** y dispara notificación por canal secundario (ver 5.4).
3. Cada evento P0/P1 lleva `escalation_level` (0 = responsable, 1 = respaldo, 2 = jefe de área) y `ack_deadline` en el schema (sección 4).
4. El roster de guardia (quién es responsable/respaldo por UCI y turno) vive en una tabla `guardia_activa`, no en el evento — el Escalation Worker la consulta al momento de escalar para reflejar cambios de turno en curso.

**Por qué no basta con "entregar el mensaje":** el requerimiento original (README, problema #2) es "localizar y contactar rápidamente al responsable, y activar un flujo alternativo si no está disponible". Delivery ≠ atención humana confirmada.

---

## 4. Schema del Evento

```json
{
  "event_id": "uuid-v4",
  "event_type": "DIAGNOSTICO | ALERTA_EMERGENCIA | ALERTA_EVOLUCION | ALERTA_TURNO",
  "priority": "P0 | P1 | P2",
  "hospital_id": "HOSP-AAA",
  "region": "LIMA-CENTRO",
  "distrito": "SAN ISIDRO",
  "uci_id": "UCI-01",
  "patient_id": "anonymized-hash",
  "timestamp": "ISO-8601 UTC",
  "payload": {
    "diagnostico": "string | null",
    "signos_vitales": { "fc": 0, "pas": 0, "pad": 0, "spo2": 0, "temp": 0 },
    "indicaciones": "string | null",
    "responsable_id": "string",
    "turno_actual": "MAÑANA | TARDE | NOCHE"
  },
  "metadata": {
    "retries": 0,
    "trace_id": "uuid-v4",
    "causation_id": "event_id-or-null"
  },
  "escalation": {
    "escalation_level": 0,
    "ack_deadline": "ISO-8601 UTC",
    "acked_by": "string-or-null",
    "acked_at": "ISO-8601 UTC-or-null"
  }
}
```

**Reglas de validación (Event Gateway):**
- `event_id` debe ser único (rechazar duplicados con `idempotency_key`).
- `priority` debe ser P0, P1 o P2; default P2 si no se especifica.
- `hospital_id` debe existir en el registro de hospitales activos.
- `timestamp` no puede ser futuro (>5 min de drift rechazado).

---

## 5. Cache Layer — Persistencia durante interrupciones

### 5.1 Arquitectura del Cache

```
┌──────────────────────────────────────────────────────────┐
│                  DISPOSITIVO HOSPITAL                    │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  Sensores /  │───►│ Local Cache  │───►│  Event     │ │
│  │  Diagnóstico │    │ (Redis Local │    │  Gateway   │ │
│  │  / Enfermería│    │  o SQLite)   │    │            │ │
│  └──────────────┘    └──────┬───────┘    └─────┬──────┘ │
│                             │                   │        │
│                             ▼                   ▼        │
│                      ┌──────────────┐    ┌──────────┐   │
│                      │  WAL Writer  │    │  Outbox  │   │
│                      │  (crash-safe)│    │  Pattern │   │
│                      └──────────────┘    └──────────┘   │
└──────────────────────────────────────────────────────────┘
```

### 5.2 Estrategia de Persistencia Local

**Durante operación normal:**
1. El dispositivo escribe el diagnóstico en el **cache local** (Redis con persistencia AOF o SQLite con WAL mode) **antes** de intentar enviar al Event Gateway.
2. El Event Gateway confirma el envío → el cache elimina el registro (o lo marca como `synced`).
3. Si el envío falla, el registro queda pendiente con estado `pending_sync`.

**Durante outage energético o de red:**
1. El cache local retiene registros con **WAL (Write-Ahead Logging)** que sobrevive cortes de energía.
2. Batería de respaldo (UPS) da 15 minutos para flush del WAL a disco persistente.
3. Al restaurarse energía/conectividad, un **Sync Worker** reconsume los registros pendientes en orden FIFO.

**Retención en cache:**
- Registros `synced`: eliminados después de 1 hora.
- Registros `pending_sync`: retados hasta 72 horas, luego escalar a alerta manual.
- Capacidad del cache: 50,000 registros por hospital (~50MB con compresión).

### 5.3 Entrega al médico — multi-canal con fallback

El cache/outbox de las secciones 5.1-5.2 resuelve la persistencia del **productor** (hospital). Falta el lado del **consumidor**: si el celular del médico responsable está apagado o sin señal, la alerta P0 no puede depender de un solo canal.

- **Canal primario:** push notification (APNs/FCM) + WebSocket si la app está en foreground.
- **Canal secundario (obligatorio para P0/P1 sin ACK, ver 3.1):** SMS y llamada automatizada (IVR) al número registrado del médico de turno, disparados por el Escalation Worker.
- **Registro de disponibilidad:** cada médico tiene un `device_token` y `phone_number` vigentes en el roster de guardia; el login de turno actualiza cuál médico es "responsable" vs "respaldo" para cada UCI.
- Sin este mecanismo, un evento con "delivery" exitoso al broker puede no haber llegado a ningún humano — que es exactamente el escenario que el README identifica como problema crítico #2.

### 5.4 Transactional Outbox Pattern

Para garantizar atomicidad entre escritura a BD y publicación de evento:

```
1. BEGIN TRANSACTION
2. INSERT INTO diagnostico (...) -- persistir datos
3. INSERT INTO outbox (event_type, payload, status='PENDING')
4. COMMIT
5. Outbox Poller detecta PENDING → publica a Event Gateway
6. Marca outbox como PUBLISHED
```

**Evita:** mensajes fantasma (evento publicado pero BD no persistió, o viceversa).

---

## 6. Edge Cases y Soluciones

### 6.1 Hospital caído temporalmente

| Escenario | Solución |
|-----------|----------|
| Hospital pierde conectividad | Su partición regional acumula mensajes (retención 24h). Al reconectarse, consumer group reconsume desde último offset committeado. |
| Hospital fuera por >24h | Alerta automática al equipo de soporte + migración temporal de pacientes a cola de respaldo regional. |
| Hospital reconecta con eventos desactualizados | El Event Gateway descarta eventos con `timestamp` mayor a 1h de antigüedad (stale events). |

### 6.2 Duplicación de mensajes

| Escenario | Solución |
|-----------|----------|
| Broker reenvía mensaje (at-least-once) | Consumidor verifica `event_id` en tabla `processed_events` antes de procesar. Deduplicación con TTL de 24h. |
| Retry del mismo evento desde cache | `idempotency_key` = `event_id` + `hospital_id` + `timestamp` truncado al minuto. |

### 6.3 Orden de mensajes

| Escenario | Solución |
|-----------|----------|
| Eventos del mismo paciente deben llegar en orden | Dentro de la partición del hospital, usar `patient_id` como clave de sub-ordenamiento (Kafka garantiza orden dentro de una partición; el consumer procesa en orden de offset y agrupa por `patient_id` antes de aplicar). |
| P0 interrumpe flujo de P1/P2 | Worker exclusivo de P0 con lowness queue separada. No comparte partition workers con P1/P2. |

### 6.4 Backpressure

| Escenario | Solución |
|-----------|----------|
| Pico masivo de emergencias (desastre natural) | Rate limiter en Event Gateway: 10K eventos/seg por hospital. Excedentes → cola de respaldo con TTL 5min. |
| Consumer no alcanza a procesar | Auto-scaling horizontal de consumers basado en `queue_depth / consumer_count` ratio. |
| Broker alcanza capacidad | Sharding automático de particiones. Nuevo partition cada 100K mensajes/seg. |

### 6.5 Fallo del Broker completo

| Escenario | Solución |
|-----------|----------|
| Caída del broker message queue | Failover automático a broker de standby (cluster activo-pasivo o activo-activo multi-region). |
| Pérdida de mensajes en tránsito | Transactional outbox garantiza que el evento se re-intenta desde la BD. No se pierden eventos. |
| Split-brain en cluster | Consenso Raft/ZAB con quorum. Solo el leader acepta writes. Fencing tokens previenen escrituras del antiguo leader. |

### 6.6 Coherencia del cache

| Escenario | Solución |
|-----------|----------|
| Cache local desincronizado con BD central | Reconciliación periódica cada 5 min: compara checksums de registros entre cache y BD. Diferencias → alerta + resync. |
| Paciente transferido a otro hospital | Evento de transferencia propaga `patient_id` al hospital destino. Cache local elimina registros del paciente transferido. |
| Conflicto de escritura (2 médicos actualizan mismo paciente) | **Nunca se descarta una escritura clínica.** Ambas versiones se persisten como entradas versionadas (append-only) con `vector_clock`; la UI muestra ambas y exige resolución humana si son incompatibles. Last-write-wins destruiría una indicación médica real y viola la retención de auditoría de 10 años (6.7). |

### 6.7 Seguridad y compliance

| Escenario | Solución |
|-----------|----------|
| Datos PHI en tránsito | TLS 1.3 obligatorio. Payload encriptado con AES-256 a nivel de aplicación. |
| Acceso no autorizado a cola | ACLs por hospital a nivel de consumer group: cada hospital solo puede publicar/consumir su propia partición/consumer group, no la partición de otro hospital dentro del mismo topic regional. Token de autenticación HMAC por evento. |
| Auditoría de acceso | Cada evento genera log inmutable en WAL separado. Retención 10 años (normativa salud Perú). |

---

## 7. Estrategia de Escalamiento

```
FASE 1 (Lanzamiento)          FASE 2 (6 meses)              FASE 3 (2 años)
1K hospitales                 100K hospitales                10M hospitales
─────────────────────         ─────────────────────         ─────────────────────
• 1 broker cluster           • 3 broker clusters           • Multi-cloud brokers
  (3 nodos)                    (1 por zona)                  (AWS + GCP + Azure)
• 1 cola global               • 10 colas regionales         • 100+ colas regionales
• partición por hospital_id   • partición por hospital_id   • partición jerárquica
  dentro de 10 colas             dentro de 10 colas             region+distrito
  (Lima piloto, 1K particiones) (Lima + 3 regiones)          (nacional, sin topic-
                                                              por-hospital, ver 2.3)
• Redis standalone            • Redis Cluster               • Redis Cluster + 
                                                           DynamoDB Global Tables
• 5 consumers                 • 50 consumers                • 5000+ consumers
                                                       (auto-scaling)
```

**Umbrales de escalamiento:**
- > 10K mensajes/seg → sharding automático de colas regionales.
- > 100K mensajes/seg → particionamiento geográfico del broker (multi-region).
- > 1M mensajes/seg → partitioning por distrito dentro de cada región.

---

## 8. Observabilidad

### 8.1 Métricas críticas

| Métrica | Alerta si | Acción |
|---------|-----------|--------|
| `event_delivery_latency_p99` | > 3s para P0 | Escalar consumers de P0 |
| `queue_depth_global` | > 100K mensajes | Auto-shard cola global |
| `dlq_messages_count` | > 10 por hospital | Notificar soporte hospital |
| `cache_pending_sync` | > 1000 registros | Investigar conectividad del hospital |
| `consumer_lag` | > 30 segundos | Auto-scale consumers |
| `broker_cpu_usage` | > 70% | Pre-shard particiones |

### 8.2 Tracing distribuido

Cada evento lleva `trace_id` que se propaga a través de:
- Event Gateway → Broker → Router → Cola regional (partición hospital_id) → Consumer → ACK/Escalation Worker.

Herramienta: OpenTelemetry + Jaeger/Zipkin para visualizar el flujo completo y detectar cuellos de botella.

---

## 9. Stack Tecnológico Propuesto

| Componente | Tecnología | Justificación |
|------------|-----------|---------------|
| Message Broker | Apache Kafka / Amazon MSK | Escalabilidad horizontal, retención configurable, at-least-once + deduplicación idempotente en consumidor (exactly-once end-to-end no es realista cruzando broker + cache local + reintentos manuales; ver 6.2) |
| Cache Local | Redis (con AOF) o SQLite (WAL) | Persistencia crash-safe, bajo latencia, sin dependencia de red |
| Event Gateway | Go / Rust (servicio ligero) | Baja latencia, alto throughput, bajo consumo de memoria |
| Outbox Pattern | PostgreSQL con pg_cron polling | Atomicidad BD + evento, probado en producción |
| Observabilidad | OpenTelemetry + Prometheus + Grafana | Estándar de industria, integración nativa con Kafka |
| Router | Custom service (Go/Rust) | Fan-out controlado, lógica de prioridad personalizada |

---

## 10. Resumen de Garantías

| Requerimiento | Cómo se cumple |
|---------------|----------------|
| Notificación en tiempo real | Colas priorizadas + consumer exclusivos de P0 → latencia < 2s |
| Contacto efectivo, no solo entrega (problema de medianoche) | ACK obligatorio con ventana de tiempo + escalamiento automático a respaldo/jefe de área + canal secundario SMS/IVR (secciones 3.1, 5.3) |
| Sin caídas | Replicación 3x, failover automático, DLQ + reconciliación |
| 99.9% disponibilidad | Broker multi-AZ, cache local opera sin red, outbox pattern |
| Recuperación < 5 min | Auto-scaling de consumers, failover de broker < 30s, cache local como fallback |
| Escala a 10M hospitales | Sharding geográfico, colas partitionadas, consumers stateless con auto-scale |
| Persistencia ante fallos | Cache local con WAL + UPS, outbox pattern, retención en broker 7 días |
