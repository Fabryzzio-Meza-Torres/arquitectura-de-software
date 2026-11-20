# Guía de uso: qué correr, para qué y cómo

Todo se corre desde la carpeta `paper-retrieval-reranking/`. Necesitas Python 3.10 o superior.

## Una sola vez: preparar el entorno

```bash
python -m venv .venv
.venv\Scripts\activate          # en Windows. En Linux o Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## 1. Comprobar que los scripts funcionan

```bash
python -m pytest tests -q
```

**Para qué:** confirmar que las métricas calculan bien antes de usarlas. **Qué debes ver:** `29 passed`. Si falla algo, no sigas.

## 2. Descargar, verificar y probar con un BM25 (el paso largo)

```bash
python src/run_all.py
```

**Para qué:** hace cuatro cosas seguidas y no necesitas hacer nada más.

1. Descarga NFCorpus y TREC-COVID.
2. Revisa que los archivos estén completos y guarda sus huellas en `data/MANIFEST.json`.
3. Calcula las estadísticas de cada dataset.
4. Corre un BM25 simple y mide su calidad y latencia con nuestras métricas.

**Cuánto tarda:** NFCorpus unos minutos; TREC-COVID algo más por su tamaño. Se puede dejar corriendo.

**Qué debes ver al final:** `Todo listo.` y, en cada dataset, una línea `Control BM25 ... OK`.

**Qué significa el control:** comparamos nuestro nDCG@10 del BM25 con el BM25 "flat" que publican Kamalloo et al. 2023 (arXiv 2306.07471): 0,322 en NFCorpus y 0,595 en TREC-COVID. Como nuestro BM25 no usa stemming, se espera quedar algo por debajo. Si sale parecido, nuestra evaluación mide bien. Si dice `REVISAR`, hay algo mal en los datos o en las métricas y hay que mirarlo antes de seguir.

**Qué deja:**

| Archivo | Qué es |
| --- | --- |
| `results/baseline_bm25.md` | Tabla con calidad y latencia juntas. |
| `results/<dataset>/stats.json` | Estadísticas y un ejemplo real de cada dataset. |
| `results/<dataset>/bm25_*.run` | Los resultados del BM25, en el formato que usará todo el equipo. |
| `results/<dataset>/bm25_*.summary.json` | Métricas y latencia de esa corrida. |

Variantes útiles:

```bash
python src/run_all.py --datasets nfcorpus     # solo el pequeño, para probar rápido
python src/run_all.py --skip-download         # si los datos ya están en data/
```

## 3. Evaluar cualquier sistema (lo usa todo el equipo)

Cada experimento guarda sus resultados en dos archivos y se evalúa con un comando:

```bash
python src/evaluate.py --qrels data/nfcorpus/qrels/test.tsv ^
    --run results/mi_sistema.run --latency results/mi_sistema.latency.tsv --out results/mi_sistema
```

**Para qué:** sacar P@3, nDCG, MRR, Recall y la latencia (p50, p95, p99) con las mismas reglas para todos. (En Linux o Mac cambia `^` por `\`.)

Los dos archivos de entrada:

- **`.run`**: una línea por documento: `id_query Q0 id_documento posición puntaje nombre`.
- **`.latency.tsv`**: una línea por consulta: `id_query<TAB>milisegundos<TAB>estado`, con estado `ok`, `degraded`, `timeout` o `error`.

Si usas el código, `write_run()` de `src/io_formats.py` escribe el `.run` por ti.

## 4. Comparar dos sistemas

```bash
python src/significance.py --a results/a.per_query.csv --b results/b.per_query.csv ^
    --metrics P@3 nDCG@10 --names A B
```

**Para qué:** saber si la diferencia entre dos sistemas es real o casualidad. Mira la columna `p (Holm)`: menor a 0,05 indica diferencia real. El intervalo dice cuánto mejora.

## 5. Tablas y gráficos para el paper

```bash
python src/report.py --from-dir results/e1 --out-dir results/reporte_e1
```

**Para qué:** juntar todos los sistemas de una carpeta en una tabla y cinco gráficos fáciles de leer. Qué deja en `results/reporte_e1/`:

| Archivo | Qué muestra |
| --- | --- |
| `tabla_principal.md` | Calidad y latencia en la misma fila; en negrita el mejor valor de cada columna. |
| `fig1_calidad_vs_latencia.png` | El gráfico central: P@3 contra p99. Arriba a la izquierda es mejor. |
| `fig2_metricas.png` | Todas las métricas de calidad por sistema. |
| `fig3_latencia.png` | p50, p95 y p99 por sistema. |
| `fig4_escalabilidad.png` | Latencia y calidad al crecer el corpus (solo si usaste `corpus_size`). |
| `fig5_candidatos.png` | Qué tan bien deja el retrieval al reranker. |
| `figuras.md` | Cómo leer cada gráfico y los datos clave. |

Para que los colores y nombres salgan bien, evalúa cada sistema con `--meta system=... group=...` (ver `05-formatos-para-el-equipo.md`).

## 6. Revisión manual (una vez, con los runs principales)

```bash
python src/review_sample.py sample --qrels data/nfcorpus/qrels/test.tsv ^
    --queries data/nfcorpus/queries.jsonl --corpus data/nfcorpus/corpus.jsonl ^
    --runs results/a.run results/b.run --out results/review.csv
```

Abre `review.csv`, llena la columna `label` con 0 (no relevante), 1 (relevante) o 2 (muy relevante) y luego:

```bash
python src/review_sample.py merge --csv results/review.csv --out results/review.qrels.tsv
```

Para evaluar con esos juicios añade `--extra-qrels results/review.qrels.tsv` a `evaluate.py`.

**Para qué:** los datasets no juzgaron todos los documentos. Esto mide cuánto cambian los resultados al juzgar los que faltaban.

## 7. Submuestras (E6 y la comparación de arquitecturas)

```bash
python src/subsample_corpus.py --data-dir data/trec-covid --sizes 40000 80000 --seed 42
```

**Para qué:** medir latencia con corpus de distintos tamaños. Crea `data/trec-covid-40000/` y `data/trec-covid-80000/`, anidadas y con semilla fija, que conservan los documentos relevantes. El tamaño mínimo posible lo dice el propio script si pides uno demasiado chico.

## 8. Comparar base contra propuesta (one-pagers)

```bash
python src/subsample_corpus.py --data-dir data/fiqa --sizes 8000 --seed 42 --keep judged
python src/onepagers.py check --data-dir data/fiqa-8000 --onepagers data/fiqa-8000.onepagers.jsonl
python src/onepagers.py build --data-dir data/fiqa-8000 --onepagers data/fiqa-8000.onepagers.jsonl
python src/compare_rankings.py compare --qrels data/fiqa-8000-onepager/qrels/test.tsv ^
    --lexical results/lexico.run --base results/base.run --proposed results/propuesta.run --out results/comparacion
```

**Para qué:** que las dos arquitecturas lean los mismos one-pagers y ver, en una tabla, quién gana y en cuántas consultas gana el léxico solo. Los one-pagers los genera el equipo antes de medir; aquí solo se validan. Detalle en `07-comparacion-arquitecturas.md`.

## Si algo falla

| Síntoma | Qué hacer |
| --- | --- |
| `ERROR` al descargar | Revisar la conexión y repetir; los archivos ya bajados no se vuelven a bajar. |
| `md5 no coincide` | Avisar al equipo y borrar `data/_zips/` para descargar de nuevo. |
| `REVISAR` en el control | Avisar a Gianpier antes de usar los resultados. |
| `Faltan N one-pagers` | Generar los que faltan; sin cobertura completa la comparación queda sesgada. |
