# Brain — Curso Arquitectura de Software

Memoria acumulada entre laboratorios. Antes de empezar un laboratorio nuevo, leer esto entero.
Cada semana se agrega una sección `## Lab N / SN — lecciones` al final. No se borra nada de lo
anterior salvo que quede obsoleto por un cambio explícito de enfoque (en ese caso, tachar con
`~~texto~~` y anotar por qué, no eliminar).

## Convenciones del repo (verificar que sigan vigentes)
- Carpetas en minúscula: `agents/`, `personas/`, `requirements/`, `reportes/`, `study-case/`.
- Los "agentes" evaluadores viven como prompts en Markdown (`agents/eval-spec.md`), no como código.
- Los requerimientos van en `requirements/functional-requirements.md` y
  `requirements/no-functional-requirements.md` (sic — el nombre del segundo archivo tiene un typo
  histórico, "Nonunctional"; no renombrarlo sin querer al copiar/pegar rutas).
- Formato de tabla de requerimientos: solo `ID | Texto del requisito`. Todo criterio de
  aceptación, umbral medible o caso borde va **embebido en el texto del requisito**, no en
  columnas separadas.
- Los reportes de evaluación de cada iteración van en `reportes/reporte-iteracion-NN.md`.

## Cómo escribir buenos requerimientos (funcionales y no funcionales)

Extraído de lo que sí funcionó y lo que costó corregir en `requirements/functional-requirements.md`
y `requirements/no-functional-requirements.md`. Usar esto como checklist al redactar un requisito
nuevo, no solo al auditarlo después.

### La forma que terminamos usando: requisito autocontenido
Cada fila es `ID | Texto`, sin columnas separadas de criterio de aceptación. Eso obliga a que el
criterio de aceptación, el umbral medible y el caso borde vivan **dentro del mismo texto**. Patrón
que se repite en los requisitos que quedaron bien (ver RF-04, RF-08, RF-09, RNF-04a/b):

1. **Trigger** — qué evento dispara el comportamiento ("ante un evento crítico...", "si el
   checklist queda incompleto 15 minutos antes del cierre...").
2. **Acción esperada del sistema** — verbo concreto y medible ("debe emitir alertas push...",
   "debe bloquear la asignación...").
3. **Umbral numérico** — tiempo, cantidad o porcentaje explícito ("en menos de 2 segundos",
   "hasta 3 veces con intervalo de 10 segundos"). Sin número, no es verificable.
4. **Caso borde / fallo** — qué pasa si la acción principal no se puede completar ("si el
   guardado falla por pérdida de conexión...", "si un destinatario está desconectado...").
5. **Resultado observable** — qué queda registrado o visible al final (log de auditoría, estado
   en pantalla, notificación a un tercero).

Un requisito que solo tiene 1-2 no pasa de intención de producto. Uno con las 5 partes es
verificable por un tester sin tener que inventar nada.

### Reglas concretas (derivadas de lo que el auditor penaliza)
- **Atomicidad**: un requisito = un comportamiento verificable. RF-08 y RF-09 casi se
  sobre-extendieron (detección + clasificación + alerta + degradación + escalamiento) — se
  mantuvieron porque cada cláusula sigue siendo una condición-acción propia y aparte, no una
  lista de features distintas disfrazada de una. Si notas que estás usando "y además" para meter
  una feature que no depende del trigger original, es candidato a partirlo en dos IDs.
- **No ambigüedad**: nada de "rápido", "adecuado", "amigable", "debería intentar". Siempre verbo
  en modo obligatorio ("debe") + condición objetiva. Compara RF-06 ("en menos de 3 segundos por
  unidad hospitalaria") contra una versión ambigua ("debe generarse rápidamente").
- **Verificabilidad**: todo umbral debe ser un número que un test automatizado pueda chequear
  (segundos, minutos, reintentos, porcentaje). Si el umbral no existe en el texto, no existe para
  efectos de evaluación — no asumir que "es implícito".
- **Caso borde explícito, no asumido**: red caída, dato ausente, permiso denegado, reintento
  agotado. RF-01 ("si el guardado falla por pérdida de conexión, debe almacenar el borrador
  localmente y reintentar...") y RNF-04b (reintento con tope + degradación a canal alternativo)
  son la plantilla: siempre trigger de falla → acción de mitigación → tope → resultado si el tope
  se agota.
- **Trazabilidad entre requisitos, sin duplicar contenido**: cuando un RF depende de un umbral ya
  definido en otro requisito (ej. RF-08 reutiliza el umbral de 2s de RNF-04a en vez de redefinirlo),
  se referencia por ID en vez de copiar el número. Evita que dos requisitos queden con umbrales
  distintos para lo mismo tras una edición futura.
- **Sin redundancia ni contradicción**: si dos requisitos regulan el mismo evento con umbrales o
  reglas distintas, es un defecto grave (bloque D en `eval-spec.md`), no una "cobertura extra".
  Antes de agregar un requisito nuevo, buscar si ya existe uno que toque el mismo trigger.
- **RNF con mecanismo de degradación, no solo el caso feliz**: RNF-03 no solo define el
  performance objetivo (<1s hasta 500 solicitudes concurrentes), define qué pasa al superar el
  umbral (degradar con indicador de carga, tope de 3s) en vez de fallar o quedar indefinido. Un
  RNF de performance/disponibilidad que no dice qué pasa al romperse el límite está incompleto.
- **Todo RNF numérico debe trazar a una meta del caso de estudio** (ver lección #6 abajo) — no
  inventar un umbral porque "suena razonable"; derivarlo de las metas de escalabilidad/performance
  del enunciado o de un RF relacionado.

### Errores concretos que ya cometimos y no repetir
- Poner el criterio de aceptación en una columna aparte del enunciado → si se pierde esa columna
  (como pasó al simplificar la tabla), el requisito deja de ser autocontenido. Ahora todo va en el
  texto mismo.
- Meter el mapeo a personas dentro del requisito o en una columna dedicada → sesga al evaluador
  (ver lección #1). El requisito no debe decir "para Rensso y Mariel"; la relevancia se deriva
  después, comparando el texto contra las necesidades de cada persona.
- Definir un umbral de tiempo distinto para el mismo evento en dos requisitos (ej. tiempo de
  entrega de alerta crítica) — currently se evita haciendo que un RF reference el RNF que ya fija
  ese número, en vez de reescribirlo.

## Lecciones transversales (aplican a cualquier laboratorio)

### 1. No pre-etiquetar lo que un evaluador (LLM) debe inferir
En la Iteración 02 los requerimientos tenían una columna "Personas / trazabilidad" que
mapeaba cada requisito a personas específicas. Se eliminó a propósito: le decía al LLM
evaluador qué personas elegir, sesgando el análisis hacia confirmar la intención del autor
en vez de auditarla de forma independiente. **Regla general:** si un agente debe *juzgar*
una relación (relevancia, cobertura, prioridad), no le des esa relación como dato de entrada
ya resuelta — dale las piezas crudas (personas, requisitos) y que la derive él mismo.

### 2. Evita drift entre la rúbrica documentada y lo que realmente se ejecuta
`reporte-iteracion-02.md` usaba una escala de puntaje (máx. ~26-28 por requisito, bloques con
máximos distintos) que ya no coincidía con lo que decía `eval-spec.md` en ese momento (máx. 20).
Un agente evaluador es inútil si su rúbrica no es la fuente única de verdad. **Regla:** cuando
se edite un agente evaluador, revisar el último reporte generado para confirmar que la
rúbrica documentada es la que realmente se está aplicando; si difieren, el reporte viejo queda
obsoleto y hay que decirlo explícitamente, no dejarlo como referencia ambigua.

### 3. Puntajes parciales siempre deben venir con "camino a 10/10"
Un evaluador crítico sin score binario es más útil, pero solo si cada nota por debajo del
máximo explica *exactamente* qué cambiar para llegar al máximo. Una fila con score < máximo y
sin esa explicación se considera una evaluación inválida/incompleta. Esto aplica a cualquier
rúbrica que se diseñe en este curso, no solo a `eval-spec.md`.

### 4. Gaps de cobertura se detectan aparte del scoring por requisito
Si el análisis solo puntúa pares (requisito, persona) que ya existen, nunca vas a detectar una
necesidad de una persona que **ningún** requisito cubre — el gap de cobertura cero es invisible
para un scoring que solo mira lo que sí está escrito. Por eso el flujo de evaluación separa un
"Paso 0" (matriz de cobertura persona × necesidad) del scoring detallado por requisito.

### 5. Estructura consistente de personas
Cada persona en `personas/*.md` sigue las mismas secciones: Datos generales, Objetivos,
Frustraciones, Escenario de uso típico, Necesidades frente al sistema, Nivel técnico. La
sección "Necesidades frente al sistema" es la lista canónica que cualquier auditoría de
cobertura debe usar como checklist — no inventar necesidades que no estén ahí, ni ignorar
alguna.

### 6. El caso de estudio fija metas numéricas que cualquier requisito debe poder trazar
Del `study-case/LAB 01 - ARQ - 2026.2.md`: escalar de 1,000 a 100,000 hospitales en 6 meses y a
10,000,000 en 2 años; app start < 1s; config de nuevo hospital < 5s; disponibilidad 99.9%;
recuperación < 5 min. Cualquier RNF de performance/escalabilidad debe poder mapearse a una de
estas metas — si no puede, probablemente está inventando un umbral arbitrario en vez de derivarlo
del caso de estudio.

## Lab1 / S1 — lecciones
- Trabajo hecho: definición de personas (4), requisitos funcionales (RF-01..RF-11 → luego
  simplificados a RF-01..RF-08 sin columnas extra), requisitos no funcionales (RNF-01..RNF-10 →
  RNF-01..RNF-08), y el agente auditor `agents/eval-spec.md`.
- Cambio de diseño clave de esta semana: remover la columna de trazabilidad de personas de los
  requerimientos (ver lección #1 arriba) — fue un error identificado por el propio usuario tras
  ver que sesgaba al evaluador.
- Si en Lab2/S2 se reintroduce algo parecido a una columna de trazabilidad "para documentación
  humana", recordar separarla claramente de lo que consume el agente evaluador, o excluirla
  explícitamente en el prompt del agente (como ya hace `eval-spec.md` en su sección de
  Restricciones).
