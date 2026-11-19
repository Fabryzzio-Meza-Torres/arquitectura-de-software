# Calidad y comparación de arquitecturas (sobre `paper/khipu`)

Parte de **datos, métricas y evaluación** del paper. Se apoya en lo que ya hay en `paper/khipu` (el BM25, el modelo
de embeddings y el α de `minion_bench.py` y `alpha.json`); no los duplica ni los cambia. Se ejecuta desde
`paper/khipu/`. Reglas y formatos: `docs/`.

## Qué se compara

Mismo dataset (one-pagers), mismas consultas y **mismos candidatos** (unión de los top 10 de BM25 y de bge, como en
el sistema). Solo cambia el score semántico:

| | Score léxico | Score semántico | Se ordena con |
| --- | --- | --- | --- |
| Base | BM25 del sistema | embeddings bge | (1-α)·léxico + α·embeddings |
| Propuesta | el mismo BM25 | sLLM local, por one-pager | (1-α)·léxico + α·sLLM |
| Referencia | el mismo BM25 | no lleva | solo léxico |

Los dos α salen de **dev**, no de test. La base usa el de `alpha.json` (0,85). El de la propuesta se elige con
`compare_rankings.py alpha` sobre dev y se congela antes de mirar test; sus scores tienen otra escala. Que la
propuesta mejore a la base es una **hipótesis**: se reporta con números, gane o no.

## Cómo puntúa el sLLM (no es binario)

Técnica **RG-S** (relevance generation con escala 0-4; Zhuang et al., arXiv 2310.14122). Al modelo se le pide una
etiqueta de 0 a 4 y se leen las probabilidades que asigna a cada una en una sola pasada, sin generar texto. El score
es la esperanza `E = Σ k·p_k / 4`: un número continuo entre 0 y 1, con pocos empates. Se normaliza min-max por
consulta antes de fusionar, igual que los embeddings. Un modelo que reparte menos de 0,5 de probabilidad entre los
dígitos 0-4 no está respondiendo la escala: esos casos se cuentan y se reportan como "degraded".

**Batches:** el profe pidió probar **4 y 10** (`--modo lote4` y `--modo lote10`). Con 20 candidatos son 5 y 2 pasadas.
Cada documento va en su propio prompt, así que el score debe salir igual; solo cambia la latencia (hay una prueba).

## Dataset elegido: FiQA-2018, submuestra de 8.000 documentos

- Ya es del paper, tiene dev (500 consultas; ahí se eligió el α del sistema) y test (648), y 1 a 3 relevantes por
  consulta. Por eso una submuestra puede **conservar todos los relevantes de dev y test** (unos 3.000 documentos, según
  las estadísticas de BEIR; sin verificar aquí) y completar al azar hasta 8.000.
- TREC-COVID no sirve para esto: tiene ~490 documentos juzgados por consulta (24 mil en total), más que la submuestra,
  y no trae dev.
- Límite: los documentos de FiQA son cortos (≈130 palabras de promedio), así que el one-pager comprime poco. El prompt
  pide máximo 90 palabras y conservar los datos; hay que revisar una muestra a mano.
- Con 8.000 documentos la tarea es más fácil que con el corpus completo; los números no son comparables con BEIR.

## Paso a paso

```bash
# 0. Submuestra de 8.000 con los relevantes de dev y test (el train se ignora para no pasarse de 8.000)
python calidad/src/subsample_corpus.py --data-dir data/fiqa --sizes 8000 --keep-splits dev test      # -> data/fiqa-8000

# 1. One-pagers (GPU). Primero una prueba corta: imprime docs/s y el tiempo que falta
python calidad/src/generar_onepagers.py --data-dir data/fiqa-8000 --modelo Qwen/Qwen2.5-3B-Instruct \
    --out data/fiqa-8000.onepagers.jsonl --max-docs 64
python calidad/src/generar_onepagers.py --data-dir data/fiqa-8000 --modelo Qwen/Qwen2.5-3B-Instruct \
    --out data/fiqa-8000.onepagers.jsonl                 # retoma donde quedó
python calidad/src/onepagers.py check --data-dir data/fiqa-8000 --onepagers data/fiqa-8000.onepagers.jsonl
python calidad/src/onepagers.py build --data-dir data/fiqa-8000 --onepagers data/fiqa-8000.onepagers.jsonl
#    crea data/fiqa-8000-onepager/. Para que minion_bench.py y candidatos.py lo lean como "fiqa":
#    copiarlo/enlazarlo a <otro-data>/fiqa/ y usar ese --data-dir en los pasos siguientes.

# 2. Candidatos con los dos scores (GPU), en dev y en test
python calidad/src/candidatos.py --dataset fiqa --data-dir data1p --split dev  --out calidad/out/fiqa
python calidad/src/candidatos.py --dataset fiqa --data-dir data1p --split test --out calidad/out/fiqa

# 3. Score del sLLM sobre esos mismos candidatos, con batch 4 y batch 10 (dev y test)
python calidad/src/llm_semantico.py --candidatos calidad/out/fiqa.dev.candidatos.jsonl --data-dir data1p \
    --dataset fiqa --modelo Qwen/Qwen2.5-3B-Instruct --modo lote10 --out calidad/out/fiqa.dev.llm_lote10
#    repetir con --modo lote4 y con el split test

# 4. Elegir α de la propuesta con DEV
python calidad/src/armar_runs.py --candidatos calidad/out/fiqa.dev.candidatos.jsonl \
    --llm calidad/out/fiqa.dev.llm_lote10.scores.jsonl --out calidad/out/dev
python calidad/src/compare_rankings.py alpha --qrels data1p/fiqa/qrels/dev.tsv \
    --lexical calidad/out/dev/lexical.run --semantic calidad/out/dev/llm.run --out calidad/out/alpha_llm

# 5. Rankings de TEST con ese α y comparación
python calidad/src/armar_runs.py --candidatos calidad/out/fiqa.test.candidatos.jsonl \
    --llm calidad/out/fiqa.test.llm_lote10.scores.jsonl --alpha-llm <α elegido> --out calidad/out/test
python calidad/src/compare_rankings.py compare --qrels data1p/fiqa/qrels/test.tsv \
    --lexical calidad/out/test/lexical.run --base calidad/out/test/base.run --proposed calidad/out/test/proposed.run \
    --out calidad/out/comparacion

# 6. Calidad por condición y ruta con los registros de latencia que ya existen (fitness ii y costo de las fallas)
python calidad/src/calidad_por_ruta.py --results results/fiqa --qrels data/fiqa/qrels/test.tsv --out calidad/out/fiqa_ruta
```

(`data1p` es el directorio de datos donde `fiqa/` es el dataset de one-pagers, para no pisar el original.)
El tiempo del sLLM queda en `*.tiempos.tsv` (qid, ms, estado) y se resume con `evaluate.py`/`latency.py`.

## Dónde correrlo: Kaggle o Khipu (cada quien elige)

Todo está en `src/pipeline.py`, que no depende de la plataforma. Kaggle y Khipu solo lo envuelven. El primer paso
(`verificar_modelo.py`) prueba en 1-3 minutos que el modelo carga, que responde con un dígito 0-4, que distingue un par
obviamente relevante de uno irrelevante, que genera un one-pager y que un batch de 10 cabe en la GPU. Si el modelo
preferido falla, usa el siguiente de la lista; si ninguno sirve, se detiene ahí y no después de horas. Si la GPU se
queda sin memoria a mitad de corrida, el batch se parte en dos y sigue. Los archivos de salida se escriben completos o no
existen (`.part`), así que reiniciar retoma sin tomar un archivo cortado por bueno.

**Kaggle** (`kaggle-calidad/`): `bash kaggle-calidad/preparar_dataset.sh`, subir el dataset `minion-calidad` (más el
`minion-bench` que ya existe) y `kaggle kernels push -p kaggle-calidad`. Con `SMOKE = True` primero; luego `False`.
Cada persona usa su propia cuenta: cambiar `gianpiersegoviaureta` por su usuario en los dos `*-metadata.json`.
Resultado: `/kaggle/working/calidad_results.tar.gz`.

**Khipu** (`khipu_preparar.sh` y `khipu_correr.sbatch`): se prepara en el nodo de acceso (con internet) y se lanza con
`sbatch`. Los scripts de Khipu **no se probaron en una sesión real**: revisar partición y GPU con `sinfo` y `myaccount`.

**En cualquier PC con GPU:** `python calidad/src/pipeline.py --work-dir <carpeta> [--smoke] [--size 8000]`.

**Mismos datos para todos.** FiQA se baja de BEIR y la submuestra usa semilla 42, así que sale igual para todos con el
mismo `--size`. Los one-pagers viven **en el repo**, en `calidad/data/onepagers_fiqa_8000.jsonl` (≈5 MB): si el archivo
existe, `pipeline.py` lo usa y no genera nada, así todos miden sobre los mismos textos y nadie tiene que compartir zips.
Para crearlo entre varias personas, cada una corre su parte en su Kaggle/Khipu:

```bash
python calidad/src/pipeline.py --work-dir <carpeta> --shard 1/3     # persona 1 (otra 2/3, otra 3/3)
# cada una sube su calidad_out/onepagers_8000.shardXde3.jsonl a calidad/data/; después, una sola vez:
python calidad/src/onepagers.py merge --inputs calidad/data/onepagers_8000.shard*de3.jsonl --out calidad/data/onepagers_fiqa_8000.jsonl
```

`merge` se niega si las partes mezclan modelos o prompts distintos, así que todo el corpus queda generado con lo mismo.
Los **tiempos** del sLLM solo se comparan entre corridas con la misma GPU (queda en `entorno.json`); la calidad (P@3) casi
no depende de la GPU. Para que la latencia sea comparable con la del equipo, usar la T4 de Kaggle.

**Tamaño de la submuestra:** es un parámetro (`--size`; 8.000 por defecto, 10.000 también sirve). Los relevantes de dev y
test (~3.000) se conservan siempre. Más documentos alargan los one-pagers, los embeddings y el BM25, pero no el scoring
del sLLM (que depende de las consultas, no del corpus).

## Qué deja al terminar (cada quien genera su reporte)

El último paso del pipeline (`reporte_final.py`) escribe en `calidad_out/reporte/`: `reporte.md` (tabla de las tres
arquitecturas, la diferencia propuesta menos base con su IC 95 %, latencia del sLLM por batch, % de scores degradados y los
límites del experimento) y cuatro gráficos: calidad por arquitectura, peso α del léxico, latencia por batch y reparto de los
scores del sLLM. Nadie tiene que armar nada a mano ni mandar archivos a otra persona. Si se quiere regenerar:
`python calidad/src/reporte_final.py --out-dir <work>/calidad_out --qrels <work>/data1p/fiqa/qrels/test.tsv`.

## Los prompts

Score semántico (RG-S, `PROMPT_RGS` en `src/llm_semantico.py`; el modelo responde con un dígito):

```
You are a search relevance judge. Rate how well the document answers the query on a scale from 0 to 4:
0 = not relevant, 1 = related topic but does not answer, 2 = partially answers, 3 = answers well, 4 = answers perfectly.
Reply with a single digit.

Query: {query}

Document:
{one-pager del documento}

Rating (0-4):
```

One-pager (`PROMPT_ONEPAGER` en `src/generar_onepagers.py`):

```
Write a one-page digest of the document below in at most {90} words, in English. Include: the main topic, the key facts,
figures and named entities, and what questions the document can answer. Use only information that is in the document.
If the document is already short, keep all of its key details.

Title: {título}

Document:
{texto}

Digest:
```

Ambos van dentro de la plantilla de chat del modelo (mensaje de usuario). La huella del prompt queda en cada línea de salida.

## Tiempo estimado (NO medido: aquí no hay GPU)

Orden de magnitud con un modelo de ~3B en una T4: one-pagers de 8.000 documentos, de media hora a una hora; scoring RG-S
de dev + test (≈1.150 consultas × hasta 20 candidatos, solo lectura sin generar texto), de media hora a una hora por
modelo; el resto, minutos. Total para dos tamaños de modelo y los dos batches, en el orden de 3 a 4 horas. Es una
cuenta de escritorio: las pruebas cortas (`--max-docs 64`, `--max-queries 20`) dan el ritmo real antes de lanzar todo.
Si no cabe, se reduce con `--max-queries` (p. ej. 300 de test) o con el modelo más chico.

## Qué falta y qué no se pudo probar

- Nada de esto corrió con datos ni modelos reales; solo con datos de juguete (`pytest calidad/tests`, 60 pruebas), que
  incluyen la equivalencia de la fusión de la base con `Engine.fuse` y que batch 4 y batch 10 dan los mismos scores.
- Hay que **fijar el modelo** antes de mirar test, y anotar su id exacto. Probar dos tamaños es lo ideal.
- Confirmar con el profe el tamaño de la submuestra (8.000 es lo que dijo).
- El BM25 de `src/bm25_baseline.py` (k1=1,2, b=0,75, sin stemming) es solo el control contra el valor publicado de BEIR.
  Para "solo léxico" se usa el BM25 del sistema (k1=0,9, b=0,4, con stemming).

## Mapa

`src/`: `pipeline`, `reporte_final`, `verificar_modelo`, `subsample_corpus`, `generar_onepagers`, `onepagers`, `candidatos`, `llm_semantico`, `armar_runs`,
`compare_rankings`, `calidad_por_ruta`, `metrics`, `evaluate`, `significance`, `latency`, `report` y utilidades.
`docs/`: reglas de evaluación (02), comparación de arquitecturas (07) y el resto de la guía.
