# Trabajos 2 y 3 — Latencia y fallas (Khipu) · Personas 2 y 3

Paper: **MINION: Parallel Hybrid Retrieval and Reranking under a Latency Budget**.

| | Dataset | Nodo preferido | Cuenta |
|---|---|---|---|
| **Trabajo 2 — Persona 2** | FiQA-2018 | g002 (RTX A6000) | la de la Persona 2 |
| **Trabajo 3 — Persona 3** | TREC-COVID | ds001 (RTX A6000) | la de la Persona 3 |

**Cada trabajo es independiente.** Cada persona escribe y corre su **propio** script siguiendo esta misma especificación, con su propia cuenta. Nadie espera código, índices ni resultados de otro: cada job descarga sus datos, arma sus índices, calibra y mide. La especificación es idéntica para que los dos scripts se comporten igual.

La calidad (P@3) de cada ruta se calcula en el Trabajo 1, en Kaggle. Aquí **solo se mide tiempo y continuidad**.

**α ya está fijado.** Las corridas finales **cargan `alpha.json`** (α = 0,85, ajustado en FiQA-dev, job Slurm 63761) y usan la misma configuración de recuperación y fusión que registró ese ajuste (sección 2). Así las listas que devuelve el servicio son las mismas que evalúa el Trabajo 1. **No se vuelve a ajustar α.**

**Tiempo estimado:** ~4 h para escribir y probar el script en la laptop + ~3 h de job en Khipu + ~1 h para el notebook de análisis. El notebook se puede escribir **mientras corre el job**, usando los logs del piloto.

---

## 0. Instrucciones si este archivo se le pasa a una IA

- **No ejecutes nada en Khipu** hasta que la sección 1 tenga todas sus respuestas. Si falta alguna, pregunta y espera.
- Los valores de las secciones 2 y 3 están **congelados**. No los cambies; si uno parece un error, avisa al humano.
- **Nunca** pidas, escribas ni uses contraseñas. El acceso a Khipu es **solo con la llave SSH del humano**. Si no hay una llave configurada, detente y explícale cómo crearla (`ssh-keygen` + `ssh-copy-id`), dejando que la contraseña la escriba el propio humano. Más de 3 intentos fallidos pueden bloquear la IP.
- El **nodo de acceso** sirve solo para instalar y descargar. Todo cómputo va por `sbatch`.
- Primero el script debe funcionar **en la laptop** con un subconjunto (por ejemplo, 2.000 documentos y 1 minuto por condición). Recién después va a `debug-gpu` y luego al job real.
- Sigue la skill `khipu`: consultar `myaccount`, `sinfo` y `squeue` antes de pedir recursos, y distinguir lo observado de lo estimado.
- Reporta solo lo que se ejecutó de verdad.

## 1. Decisiones del humano (bloqueantes)

| # | Pregunta | Respuesta |
|---|---|---|
| H1 | Usuario de Khipu (solo el nombre) y ¿ya entra por SSH **con llave**? | ____ / sí-no |
| H2 | Salida de `myaccount` y `sinfo`: ¿qué particiones y qué **`--account`** de Slurm puede usar la cuenta? ¿Tiene acceso a `data-science` (ds001)? | ____ |
| H3 | Si el nodo preferido sigue ocupado a las 13:00, ¿qué se usa? (a) el otro A6000, (b) ag001 con MIG `a100_2g.10gb` (ya funcionó en el job 63761), (c) cualquier GPU libre y se reporta, (d) la PC propia dedicada | ____ |
| H4 | Capacidad C medida en la calibración (la llena el script, pero el humano la confirma antes de las repeticiones) | ____ QPS |
| H5 | ¿Ya está `alpha.json` copiado en la carpeta del proyecto en Khipu (`scp alpha.json <usuario>@khipu.utec.edu.pe:<proyecto>/`)? | sí / no |

## 2. Configuración congelada (idéntica en los 3 trabajos)

```json
{
  "seed": 42,
  "datasets": {
    "fiqa":       "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/fiqa.zip",
    "trec-covid": "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/trec-covid.zip"
  },
  "doc_text": "title + ' ' + text",
  "lexical":  {"lib": "bm25s", "method": "lucene", "k1": 0.9, "b": 0.4, "stopwords": "en", "stemmer": "english (PyStemmer)", "top_k": 10},
  "semantic": {"model": "BAAI/bge-base-en-v1.5", "model_revision": "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
               "query_prefix": "Represent this sentence for searching relevant passages: ",
               "encoding": "forward en fp16; pooling CLS; normalización L2; se guarda en float32",
               "index": "faiss.IndexFlatIP", "max_length": 512, "top_k": 10},
  "fusion":   {"normalization": "min-max por consulta; si max == min -> 1.0", "formula": "(1 - alpha) * lex_norm + alpha * sem_norm",
               "alpha": "leer de alpha.json (= 0.85)", "tie_break": "ID del documento ascendente (como string), también en el corte del top 10"},
  "reranker": {"model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "max_length": 512, "replicas": 2, "batch": "todos los candidatos en un lote"},
  "timeouts_ms": {"lexical": 50, "semantic": 1200, "fusion": 50, "rerank": 1200},
  "slo_ms": 2500,
  "hedging": {"threshold": "p95 del reranker medido en calibración", "max_extra": 0.10, "window_s": 60}
}
```

**Al arrancar, el script:**
1. Carga `alpha.json`.
2. Verifica que `alpha == 0.85` y que sus campos `bm25`, `semantic`, `model_revision`, `normalization` y `document_tie_break` coinciden con este bloque. Si algo difiere, **se detiene con error**.
3. Copia `alpha.json` dentro de `run_meta.json`.

Para el piloto en la laptop también se usa `alpha.json`. **No hay un α provisional.**

## 3. Diseño del script (un solo archivo, `minion_bench.py`)

**Todo en un proceso con `asyncio`.** Cada etapa es una función `async` que corre su trabajo pesado en un `ThreadPoolExecutor`; PyTorch, FAISS y NumPy liberan el GIL.

```
generador de carga (Poisson, open-loop)
  └─► consulta(q):
        lex, sem = gather(wait_for(bm25(q), 50ms), wait_for(denso(q), 1200ms))
        candidatos = unión (≤ 20) → completar puntajes → min-max → fusión (wait_for 50ms)
        top3 = rerank_con_hedging(candidatos)   # plazo total 1200ms
        → ruta según la Tabla 2
```

**Rutas (Tabla 2 del paper):**

| Condición | Ruta | `route` |
|---|---|---|
| todo a tiempo | top 3 del reranker | `reranked` |
| **reranker deshabilitado a propósito** (línea base NORERANK): el reranker **no se invoca** | top 3 fusionado | `fused_baseline` |
| el reranker **se invoca** y falla o pasa 1,2 s → ruta de respaldo | top 3 fusionado | `fused_fallback` |
| la semántica falla o pasa 1,2 s, la léxica responde | top 3 léxico | `lex` |
| la léxica falla, la semántica responde | top 3 semántico | `sem` |
| fallan ambas | error controlado | `error` |

**Hedging:**
1. Enviar a la réplica A.
2. Si A no responde antes del umbral, y las copias de los últimos 60 s son menos del 10 % de las originales, enviar la misma solicitud a la réplica B.
3. Usar **la primera respuesta válida dentro del plazo de 1,2 s**, contado desde el envío a A. Si una réplica lanza una excepción mientras la otra sigue en curso, **no se descarta** la solicitud en curso: se espera su respuesta hasta el plazo. Solo cuando las dos réplicas fallaron, o se cumple el plazo sin ninguna respuesta válida, se usa la ruta `fused_fallback`.

Las réplicas son **dos instancias del modelo** en la misma GPU. Esto se declara como limitación en el paper.

**Inyección de fallas:** un diccionario por condición `{"lex","sem","rerank_a","rerank_b"} → modo`:
- `ok`
- `error`: lanza una excepción
- `delay:<ms>`: duerme ese tiempo antes de responder
- `delay_prob:<p>:<ms>`: duerme con probabilidad p

**Las demoras probabilísticas son deterministas.** Qué solicitudes se demoran se decide con `np.random.default_rng([42, rep, índice_de_solicitud])`, y el horario de llegadas usa la misma semilla. Así, **F3H y F3NH reciben exactamente las mismas llegadas y demoran exactamente las mismas solicitudes**: la única diferencia entre ambas es si se duplica o no.

**Generador de carga open-loop:** los tiempos de llegada salen de un proceso de Poisson con `np.random.default_rng(42)`. Cada solicitud se lanza como tarea en su hora programada **sin esperar a las anteriores**. La latencia se mide **desde la hora programada** (`t_sched`), no desde que la tarea empieza. Así no se esconde la cola cuando el sistema se satura.

**Consultas:**
- Calibración: FiQA → consultas de `train`. TREC-COVID → títulos de 1.000 documentos al azar (seed 42).
- Experimentos: consultas de test, recorridas de forma cíclica.

## 4. Qué corre el job

| Fase | Contenido | Duración |
|---|---|---|
| 0 | Construir el índice BM25 + los embeddings del corpus en GPU + cargar 2 réplicas + 50 consultas de calentamiento | FiQA ~10 min / TREC-COVID ~20 min |
| 1. Calibración | (a) 500 consultas a 1 QPS → p50/p95/p99 por etapa y **umbral de hedging = p95 del reranker**. (b) Rampa de 1, 2, 4, 8, 16, 32 y 64 QPS, 2 min por escalón; **C** = mayor tasa con throughput ≥ 99 % de lo ofrecido y p99 estable (la segunda mitad del escalón no es > 1,2 × la primera). Guardar en `calibration.json` y **congelar**. | ~20 min |
| 2. Repeticiones ×3 | Las 13 condiciones de la tabla siguiente, 3 min cada una, descartando los primeros 30 s | ~46 min por repetición |

| Grupo | Condición | Carga | Qué se hace | Ruta esperada |
|---|---|---|---|---|
| Carga | L25, L50, L75, L100 | 25/50/75/100 % de C | sistema completo con hedging, sin fallas | `reranked` |
| **Línea base** | NORERANK | 100 % | línea base que omite el reranker: **no se invoca** | `fused_baseline` |
| Carga | NOHEDGE | 100 % | sistema completo con hedging apagado, sin fallas | `reranked` |
| **Falla** | F1 | 75 % | el reranker **se invoca** y falla: `rerank_a` y `rerank_b` = `error` | `fused_fallback` |
| **Falla** | F2 | 75 % | el reranker **se invoca** y es lento: `rerank_a` y `rerank_b` = `delay:1500` | `fused_fallback` |
| **Hedging** | **F3H** | 75 % | `rerank_a` = `delay_prob:0.05:800`, **con** hedging | `reranked` |
| **Hedging** | **F3NH** | 75 % | **las mismas** llegadas y demoras que F3H, **sin** hedging | `reranked` |
| Falla | F4 | 75 % | `sem` = `error` | `lex` |
| Falla | F5 | 75 % | `lex` = `error` | `sem` |
| Falla | F6 | 75 % | `lex` y `sem` = `error` | `error` |

- **NORERANK y F1/F2 no son lo mismo.** NORERANK es la línea base “híbrida sin reranking” del paper. **F1 y F2 son las pruebas que verifican la fitness (iii)**: si la ruta de respaldo entrega tres resultados dentro de 2,5 s cuando el reranker falla (F1) o se demora (F2).
- **F3H vs. F3NH** mide el efecto de duplicar: se comparan el p99 de la etapa de reranking, el p99 de extremo a extremo y el % de solicitudes adicionales (solo F3H puede tenerlas).

**Total del job:** ~2,6 h (FiQA) a ~3,1 h (TREC-COVID). Pedir `--time=05:00:00` para tener margen.

## 5. Logs (mismo formato en los dos trabajos)

`requests_{dataset}_rep{r}_{condicion}.jsonl`, una línea por solicitud:

```json
{"dataset":"fiqa","rep":1,"condition":"L100","qid":"123","t_sched":0.0,"t_end":0.0,"latency_ms":0.0,
 "route":"reranked","n_results":3,"timeouts":["sem"],"errors":[],"rerank_invoked":true,"delay_injected":false,
 "hedge_sent":false,"hedge_won":false,"stage_ms":{"lex":0.0,"sem":0.0,"fusion":0.0,"rerank":0.0},"doc_ids":["d1","d2","d3"]}
```

Valores de `route`: `reranked | fused_baseline | fused_fallback | lex | sem | error`.

`run_meta.json`: nodo, salida de `nvidia-smi`, salida de `lscpu`, versiones de Python y librerías, sha256 de `minion_bench.py`, configuración completa, contenido de `alpha.json` y contenido de `calibration.json`.

`summary.csv`, una fila por (rep, condición): QPS ofrecida y lograda, solicitudes enviadas, p50/p95/p99 de las respuestas válidas (`n_results == 3`), % de errores, % de timeouts por etapa, **continuidad** = % con 3 resultados en ≤ 2.500 ms sobre **todas** las enviadas, y **% duplicadas** = `hedge_sent / originales`.

Para el p99 se usa el método del paper: ordenar los N tiempos y tomar la posición `ceil(0,99 × N)`.

## 6. Pasos en Khipu

1. **En el nodo de acceso:**
   - Crear el entorno: `python -m venv` o conda, con `torch`, `sentence-transformers`, `faiss-cpu`, `bm25s`, `PyStemmer` y `numpy`.
   - Descargar el zip del dataset y los dos modelos con `huggingface-cli download`, dejándolos en el home.
2. **Piloto en `debug-gpu`** (≤ 30 min): el script con 1 min por condición y 1 repetición. Revisar los logs.
3. **`sbatch` real.** Esqueleto (ajustar la partición según H2):
   ```bash
   #!/bin/bash
   #SBATCH --job-name=minion-<dataset>
   #SBATCH --account=<cuenta Slurm de H2>
   #SBATCH --partition=<gpu | data-science>
   #SBATCH --nodelist=<g002 | ds001>
   #SBATCH --gres=gpu:1          # en ag001: --gres=gpu:a100_2g.10gb:1 y sin --nodelist
   #SBATCH --cpus-per-task=8
   #SBATCH --mem=32G
   #SBATCH --time=05:00:00
   #SBATCH --output=logs/%x-%j.out
   export HF_HUB_OFFLINE=1
   source <entorno>/bin/activate
   srun python minion_bench.py --dataset <fiqa | trec-covid> --reps 3 --out results/
   ```
4. **Al terminar:** copiar `results/` fuera de Khipu con `scp` o `rsync`, porque Khipu no tiene backup.

## 7. Si se atrasan (recortar en este orden)

1. Bajar cada condición a 2 min.
2. Quitar NOHEDGE (la comparación con y sin duplicar ya la cubren F3H y F3NH).
3. Quitar L25 y L75.

**Nunca quiten** L100, NORERANK, F1, F3H ni F3NH: de ellas dependen las 4 fitness functions y la comparación del hedging.

## 8. Gráficas y matrices obligatorias

Se generan en la laptop con `matplotlib` a partir de los logs descargados. Van en `figs/` como PNG a 200 dpi, **mostradas dentro del notebook**. Cada una tiene título, ejes con unidades (ms, QPS, %), leyenda y una celda Markdown de 2–3 líneas: qué muestra y qué se concluye.

**Colores comunes a los 3 trabajos** (Okabe-Ito): rutas `reranked #CC79A7`, `fused_baseline #009E73`, `fused_fallback #009E73 con trama rayada`, `lex #0072B2`, `sem #E69F00`, `error #D55E00`. Niveles de carga con `viridis`. La línea del SLO de 2.500 ms y la del 99 % de continuidad van en negro discontinuo.

| # | Archivo | Qué muestra |
|---|---|---|
| K1 | `K1_rampa_{ds}.png` | Calibración: QPS lograda vs. ofrecida (con la diagonal ideal) y, en un segundo panel, p99 vs. QPS ofrecida. **C** marcada |
| K2 | `K2_etapas_{ds}.png` | Boxplot o violín de la latencia por etapa (lex, sem, fusión, rerank, extremo a extremo) a 1 QPS, con el timeout de cada etapa marcado. Compara lo medido con la Tabla 1 |
| K3 | `K3_ecdf_carga_{ds}.png` | ECDF de la latencia de extremo a extremo para L25–L100 (eje x en escala log), con la línea de 2.500 ms |
| K4 | `K4_percentiles_carga_{ds}.png` | p50, p95 y p99 vs. % de carga (mediana de 3 repeticiones, con el rango como barra de error), más NORERANK y NOHEDGE al 100 % como puntos aparte. Línea del SLO |
| K5 | `K5_serie_tiempo_{ds}.png` | Latencia de cada solicitud vs. tiempo en L100 y en F2 (repetición 1), con la zona de calentamiento sombreada |
| K6 | `K6_matriz_rutas_{ds}.png` | **Matriz** (heatmap con %): filas = las 13 condiciones, columnas = ruta usada (reranked / fused_baseline / fused_fallback / lex / sem / error). Muestra que NORERANK usa la línea base, que cada falla activa la ruta de la Tabla 2, y que **las dos no se mezclan** |
| K7 | `K7_continuidad_{ds}.png` | Barras de continuidad (%) en F1, F2 y F4–F6 (y NORERANK como referencia), con la línea del 99 % |
| K8 | `K8_hedging_{ds}.png` | **F3H vs. F3NH:** ECDF de la latencia de la etapa de reranking y de extremo a extremo, con p99 marcado; al lado, una barra con el % de duplicadas de F3H frente a la línea del 10 %. Como las llegadas y las demoras son idénticas, la diferencia se debe solo a duplicar |
| K9 | `K9_fitness_{ds}.png` | **Matriz** de semáforo: filas = fitness (i)–(iv), columnas = repeticiones 1–3. Verde si cumple, rojo si no, y el valor medido dentro de cada celda. Fuentes: (i) L25–L100; (ii) “ver Trabajo 1”; (iii) continuidad en **F1 y F2** (se muestra la peor de las dos); (iv) % de duplicadas en L25–L100 y F3H |

## 9. Notebook explicado paso a paso

`trabajo{2|3}_latencia_{ds}.ipynb`, **ejecutado con sus salidas**, que se lee de arriba abajo sin conocer el proyecto:

1. **Objetivo:** qué parte del paper responde (p99 ≤ 2,5 s, continuidad, % de duplicadas).
2. **Montaje:** hardware (sacado de `run_meta.json`), arquitectura en un diagrama de texto, configuración congelada y qué significa cada condición.
3. **Calibración:** K1 y K2, con el valor de C y el umbral de hedging elegidos.
4. **Carga:** K3, K4 y K5, más una tabla de percentiles por condición.
5. **Fallas:** K6 y K7, más una tabla de la Tabla 2 del paper contra lo observado.
6. **Hedging:** K8 y una tabla F3H vs. F3NH (p99 del reranking, p99 de extremo a extremo, diferencia en ms y % de duplicadas).
7. **Fitness functions:** K9 y una tabla que diga si cumple o no y por cuánto.
8. **Limitaciones:** réplicas en la misma GPU, todo en un proceso, una sola máquina.
9. **Conclusión:** 5–8 viñetas.

Cada celda de código va precedida por una celda Markdown que explica qué hace. Las celdas son cortas y **ningún número va escrito a mano en el texto**: todo se calcula desde los archivos.

## 10. Entregables

`trabajo{2|3}_latencia_{ds}.ipynb` (ejecutado), la carpeta `figs/`, `summary.csv`, `calibration.json`, `run_meta.json`, los `requests_*.jsonl` y el log de Slurm.

**Tabla para el paper (por dataset):** p50/p95/p99 por carga y variante (mediana y rango de las 3 repeticiones), C, umbral de hedging, % de duplicadas, y continuidad en F1–F6.
