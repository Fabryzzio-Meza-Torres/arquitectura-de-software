# RemoteSchooly / EduKanvas

Convenciones:

- **Auth:** `Authorization: Bearer <JWT>` en todo lo protegido.
- **Sync idempotente:** los `POST` de sincronización llevan header **`Idempotency-Key`** para que un reintento no duplique datos ni chunks.
- **Archivos pesados = Distribution Agent (jerárquico):** archivos partidos en **chunks** con hash; el agente local re-descarga solo los chunks que fallan (RNF-3, RNF-4, RNF-5), solicitándolos siempre al nodo superior en la jerarquía (colegio→departamento→central), sin comunicación directa entre colegios (RNF-1).
- **IA:** el `system prompt` con skills **se asume ya construido**; el AI Gateway lo aplica por dentro.

---

## 1. Endpoints por rol

### A) Profesores del gobierno — central (Lima)

| Método | Endpoint                  | Para qué sirve                                                  | RF      |
| ------ | ------------------------- | --------------------------------------------------------------- | ------- |
| `POST` | `/courses`                | Sube la currícula de un curso.                                  | G1      |
| `PUT`  | `/courses/{id}`           | Mantiene actualizada la currícula (propaga a regiones).         | G2      |
| `POST` | `/courses/{id}/publish`   | Publica un curso predeterminado de acceso público.              | G3      |
| `POST` | `/courses/{id}/materials` | Sube material (multi-formato, incluye videos).                  | G10, S6 |
| `GET`  | `/teachers/{id}/profile`  | Accede a la información del perfil de un profesor.              | G5      |
| `POST` | `/ai/generate`            | Crea material con ayuda de IA (el Sistema optimiza por dentro). | G7      |
| `GET`  | `/ai/quota?courseId=`     | Consulta el límite de tokens restante por día y curso.          | G9      |

### B) Profesores rurales — laptop-servidor (LAN)

| Método | Endpoint                        | Para qué sirve                                                                          | RF     |
| ------ | ------------------------------- | --------------------------------------------------------------------------------------- | ------ |
| `GET`  | `/courses/{id}/materials`       | Revisa los materiales del curso _(mismo endpoint que ven los estudiantes)_.             | R2     |
| `GET`  | `/courses/{id}/materials/{mId}` | Obtiene el material + manifiesto para **descargarlo offline** (vía Distribution Agent). | R1     |
| `POST` | `/classes/{id}/assignments`     | Crea tareas para la clase.                                                              | R3     |
| `POST` | `/classes/{id}/announcements`   | Crea anuncios de clase.                                                                 | R3, S5 |
| `POST` | `/schedule`                     | Programa el envío de tareas/anuncios/archivos _(lo ejecuta el Sistema)_.                | R4     |
| `POST` | `/submissions/{id}/comments`    | Registra comentarios en el entregable de un estudiante.                                 | R5     |
| `GET`  | `/notifications`                | Recibe las notificaciones del sistema.                                                  | R6     |

### C) Estudiantes

| Método | Endpoint                     | Para qué sirve                                    | RF  |
| ------ | ---------------------------- | ------------------------------------------------- | --- |
| `GET`  | `/courses/{id}/materials`    | Accede a los materiales de sus cursos (por LAN).  | E1  |
| `GET`  | `/courses?public=true`       | Accede a los cursos predeterminados del gobierno. | E2  |
| `GET`  | `/students/{id}/grades`      | Visualiza todas sus notas.                        | E3  |
| `GET`  | `/submissions/{id}/comments` | Visualiza los comentarios de sus entregables.     | E4  |

### D) Sistema / Infraestructura — "lo demás"

Endpoints y procesos que **ningún humano llama directo**; son la plomería que hace que todo funcione con internet limitado.

| Método      | Endpoint                                              | Para qué sirve                                                     | RF/RNF        |
| ----------- | ----------------------------------------------------- | --------------------------------------------------------------------- | ------------- |
| `GET`       | `/dist/{contentId}/manifest`                          | Manifiesto de chunks (índices + hash + tamaño).                     | RNF-1, RNF-3  |
| `GET`       | `/dist/{contentId}/chunks/{index}`                    | Descarga un chunk desde el nodo superior (resumible, `Range`).      | RNF-1, RNF-3  |
| `POST`      | `/dist/{contentId}/verify`                            | Reporta chunks fallidos → re-descarga solo esos desde el nodo superior (auto-retry). | RNF-3, RNF-4  |
| `GET`       | `/dist/jobs/{jobId}`                                  | Estado de la transferencia (progreso, reintentos).                  | RNF-3         |
| `POST`      | `/sync/batch`                                         | Sube por lote los cambios del aula (notas, comentarios, tareas).    | RNF-7         |
| `GET`       | `/sync/batch/{batchId}`                               | Estado del lote de sincronización.                                   | RNF-7         |
| _(interno)_ | selección de skills + modelo dentro de `/ai/generate` | Combina skills y elige el modelo más adecuado.                       | S1, S2        |
| _(interno)_ | motor del Scheduler                                   | Ejecuta los envíos programados.                                      | S3            |
| _(interno)_ | limpieza fin de bimestre · replicación push           | Libera espacio · empuja contenido a regiones.                        | RNF-8         |


---

## 2. Detalle estilo Swagger (endpoints clave del Sistema)

### `GET /dist/{contentId}/manifest`

Base del agente torrent-like: describe el contenido como una lista de chunks verificables.

- **200:**
  ```json
  {
    "contentId": "vid_123",
    "chunkSize": 4194304,
    "chunks": [
      { "index": 0, "sha256": "a1b2...", "size": 4194304 },
      { "index": 1, "sha256": "c3d4...", "size": 4194304 }
    ]
  }
  ```

### `POST /dist/{contentId}/verify`

El retry real (RNF-3): re-baja únicamente los chunks corruptos/faltantes.

- **Body:** `{ "failedChunks": [3, 7] }`
- **202:** `{ "jobId": "job_9", "status": "re-fetching", "retry": [3,7] }`

### `POST /ai/generate`

Genera material aplicando las palancas de ahorro por dentro (system prompt de skills asumido).

- **Body:** `{ "courseId": str, "prompt": str, "type": "quiz" | "lesson" | "summary" }`
- **200:** `{ "materialId": "mat_55", "cacheHit": true, "modelUsed": "small", "tokensUsed": 0, "content": "..." }`
  → `cacheHit=true` significa **0 tokens nuevos**.
- **429:** cuota de tokens agotada (RF-G9).

### `POST /sync/batch`

Sube el trabajo del aula cuando hay ventana de conexión. Idempotente.

- **Header:** `Idempotency-Key` · **Body:** `{ "grades": [...], "comments": [...], "assignments": [...] }`
- **202:** `{ "batchId": "b_12", "status": "queued" }`
- **409:** lote ya recibido (no duplica).

---
