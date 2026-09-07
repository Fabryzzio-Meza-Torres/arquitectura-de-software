# Modelo de datos — Balbuena EduKanvas (RemoteSchooly)

## 1. Diagrama Entidad–Relación

```mermaid
erDiagram
    %% ── Jerarquía Geográfica y Escolar ──
    DEPARTMENT ||--o{ SCHOOL : contains
    SCHOOL ||--o{ CLASSROOM : hosts
    COURSE ||--o{ CLASSROOM : offered_in

    %% ── Jerarquía de Usuarios y Matrícula ──
    ROLE ||--o{ USER_ACCOUNT : classifies
    USER_ACCOUNT ||--o{ TEACHER_ASSIGNMENT : assigned
    CLASSROOM ||--o{ TEACHER_ASSIGNMENT : covers
    USER_ACCOUNT ||--o{ ENROLLMENT : enrolled_as
    CLASSROOM ||--o{ ENROLLMENT : holds
    USER_ACCOUNT ||--o{ NOTIFICATION : receives

    %% ── Material Educativo y Distribución ──
    COURSE ||--o{ COURSE_PACKAGE : scopes
    SCHOOL ||--o{ COURSE_PACKAGE : receives
    COURSE_PACKAGE ||--o{ MATERIAL_FILE : bundles

    %% ── Aula Rural y Evaluaciones Físicas ──
    CLASSROOM ||--o{ ANNOUNCEMENT : publishes
    ENROLLMENT ||--o{ TASK_GRADE : evaluates
    ENROLLMENT ||--o{ PERIOD_GRADE : records

    DEPARTMENT {
        int department_id PK
        string name
    }
    SCHOOL {
        int school_id PK
        int department_id FK
        string name
        string location
    }
    COURSE {
        int course_id PK
        string name
        string grade_level "5to Primaria"
    }
    CLASSROOM {
        int classroom_id PK
        int school_id FK
        int course_id FK
        string name "Aula 1A"
    }
    ROLE {
        int role_id PK
        string name "Teacher | Student"
    }
    USER_ACCOUNT {
        int user_id PK
        int role_id FK
        string full_name
        string username
        string password_hash
        boolean is_active
    }
    TEACHER_ASSIGNMENT {
        int assignment_id PK
        int teacher_id FK
        int classroom_id FK
    }
    ENROLLMENT {
        int enrollment_id PK
        string enrollment_code "Roster ID"
        int student_id FK
        int classroom_id FK
    }
    COURSE_PACKAGE {
        int package_id PK
        int course_id FK
        int school_id FK
        string title
        string academic_period "Bimestre 1"
        int version "v1"
        string manifest_hash "SHA-256"
        string sync_state "active"
    }
    MATERIAL_FILE {
        int file_id PK
        int package_id FK
        string filename
        string file_type "PDF | video"
        bigint size_bytes
        string checksum "SHA-256"
        string storage_uri
    }
    ANNOUNCEMENT {
        int announcement_id PK
        int classroom_id FK
        string title
        string content
        datetime publish_at
    }
    TASK_GRADE {
        int grade_id PK
        int enrollment_id FK
        string task_title "Tarea fisica"
        decimal score "Nota"
        string feedback "Privado"
        datetime graded_at
    }
    PERIOD_GRADE {
        int period_grade_id PK
        int enrollment_id FK
        string period_name "Bimestre 1"
        decimal final_score "Nota final"
        datetime recorded_at
    }
    NOTIFICATION {
        int notification_id PK
        int user_id FK
        string message
        string type "sync_alert"
        boolean is_read
    }
```

---

## 2. Diccionario de entidades

### 1. Usuarios, Roles y Estructura Escolar

- **`ROLE`:** Catálogo de perfiles del sistema (`Government_Teacher`, `Rural_Teacher`, `Rural_Student`).
- **`USER_ACCOUNT`:** Credenciales y estado del usuario.
- **`DEPARTMENT`:** Región geográfica (Cusco, Loreto, etc.) para la distribución de contenidos.
- **`SCHOOL`:** Escuela rural donde opera el servidor local por LAN.
- **`COURSE`:** Asignatura que ahora incluye el grado escolar (`grade_level`), eliminando la tabla aislada `GRADE`.
- **`CLASSROOM`:** Aula física en una escuela asignada a un curso.
- **`TEACHER_ASSIGNMENT`:** Asignación del profesor rural a sus aulas.
- **`ENROLLMENT`:** Matrícula del estudiante en su aula con código visible en el roster mínimo sin perfiles expandidos (`FR-04`, `NFR-20`).

### 2. Paquetes y Contenido Educativo

- **`COURSE_PACKAGE`:** Unidad de distribución bimestral creada en Lima. Unifica el concepto de paquete, número de versión (`version`) y estado de sincronización hacia la escuela (`sync_state`: `pending`, `synchronizing`, `active`, `failed`).
- **`MATERIAL_FILE`:** Archivos educativos individuales incluidos en el paquete (videos descargables para reproducción offline, guías en PDF, fichas de trabajo) con su checksum de integridad.

### 3. Dinámica del Aula Rural

- **`ANNOUNCEMENT`:** Avisos y comunicados del docente hacia sus alumnos.
- **`TASK_GRADE`:** Registro de calificación docente para **tareas entregadas físicamente en clase**. Consolida la tarea, la nota (`score`) y la retroalimentación privada (`feedback`). El alumno no responde ni existen foros (`FR-41`).
- **`PERIOD_GRADE`:** Nota bimestral final para consulta local del alumno sin exportación ministerial (`FR-33`, `KPD-10`).
- **`NOTIFICATION`:** Alertas básicas para el docente (llegada de nuevos paquetes o alertas de sincronización).

---

## 4. Matriz de trazabilidad con requerimientos

| Requerimiento     | Descripción                                         | Soporte en el modelo                                                       |
| ----------------- | --------------------------------------------------- | -------------------------------------------------------------------------- |
| **FR-01, FR-02**  | Login por credenciales y autorización por rol/aula  | `USER_ACCOUNT`, `ROLE`, `CLASSROOM`, `ENROLLMENT`                          |
| **FR-03**         | Configuración de estructura académica por admin     | `DEPARTMENT`, `SCHOOL`, `COURSE`, `CLASSROOM`, `TEACHER_ASSIGNMENT`        |
| **FR-04**         | Roster mínimo para profesor rural                   | `ENROLLMENT.enrollment_code`, `USER_ACCOUNT.full_name`                     |
| **FR-05..08**     | Paquete bimestral con archivos multiformato         | `COURSE_PACKAGE`, `MATERIAL_FILE` (`file_type`, `storage_uri`)             |
| **FR-14..16**     | Publicación versionada y estado de distribución     | `COURSE_PACKAGE.version`, `COURSE_PACKAGE.sync_state`                      |
| **FR-17..22**     | Verificación de integridad y activación en escuela  | `MATERIAL_FILE.checksum`, `COURSE_PACKAGE.manifest_hash`, `sync_state`     |
| **FR-24, 25**     | Uso de material en aula por LAN                     | `COURSE_PACKAGE`, `MATERIAL_FILE` accesibles desde el servidor de `SCHOOL` |
| **FR-27..29**     | Anuncios y tareas del docente rural                 | `ANNOUNCEMENT`, `TASK_GRADE`                                               |
| **FR-30..32**     | Calificación y feedback de tareas físicas           | `TASK_GRADE.score`, `TASK_GRADE.feedback`                                  |
| **FR-33**         | Notas bimestrales locales                           | `PERIOD_GRADE.final_score`                                                 |
| **FR-34**         | Notificaciones básicas para el profesor             | `NOTIFICATION`                                                             |
| **FR-35, 36, 40** | Consulta privada de notas y material del estudiante | Filtrado por `ENROLLMENT` en `COURSE_PACKAGE` y `TASK_GRADE`               |
| **FR-41**         | Sin foros ni réplicas de los alumnos                | Diseño unidireccional en `TASK_GRADE` (solo lectura para el alumno)        |
