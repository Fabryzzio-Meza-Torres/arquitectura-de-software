# Cómo guardar tus resultados (para todo el equipo)

Para que mis scripts puedan medir y comparar todos los experimentos, cada sistema debe guardar dos archivos: **resultados** y **latencias**. Con `result_writer.py` se hace en pocas líneas y no hay que escribir los formatos a mano.

## Lo mínimo que tienes que hacer

```python
import sys
sys.path.insert(0, "src")                      # desde la carpeta paper-retrieval-reranking
from result_writer import ResultWriter

with ResultWriter("results/e3/cross_encoder") as rw:
    for qid, texto in queries:                 # las queries del split que estés evaluando
        with rw.request(qid) as r:             # mide solo el tiempo de este bloque
            ranking = mi_sistema(texto)        # un dict {id_documento: puntaje}
            r.set_results(ranking)
```

Al terminar quedan `results/e3/cross_encoder.run` (los resultados) y `results/e3/cross_encoder.latency.tsv` (cuánto tardó cada consulta).

## Qué va dentro del bloque `with rw.request(...)`

Todo lo que el usuario esperaría antes de recibir la respuesta: búsqueda, fusión, reranking, esperas en cola. **No** metas la construcción de índices ni la carga de modelos: eso se hace antes y no cuenta.

## Cuándo marcar un estado

| Situación | Qué hacer | Qué pasa con la calidad |
| --- | --- | --- |
| Todo normal | Nada (queda `ok`) | Se mide normal |
| Usaste el plan B (por ejemplo, devolviste el ranking del retrieval porque el reranker falló o tardó) | `r.mark_degraded()` | Se mide con lo que devolviste |
| Pasaste el plazo y no respondiste | `r.mark_timeout()` | Vale 0 en esa consulta |
| Una excepción dentro del bloque | No hagas nada: se registra como `error` y el experimento sigue | Vale 0 en esa consulta |

Esto importa para E6 (fallas inyectadas): un sistema que responde rápido porque falla no debe verse bien.

## Etapas y solicitudes duplicadas (opcional, para E5 y la propuesta con LLM)

```python
with rw.request(qid) as r:
    with r.stage("llm"):                 # mide cada ronda del LLM por separado (se puede repetir el nombre)
        scores = llm(batch)
    r.add_extra()                        # si enviaste una solicitud duplicada (hedged)
    r.set_results(ranking)
```

Se guardan en `<prefijo>.stages.tsv` y en una 4.ª columna de `.latency.tsv`. `evaluate.py` los resume solo.

## Evaluar lo que guardaste

```bash
python src/evaluate.py --qrels data/nfcorpus/qrels/test.tsv ^
    --run results/e3/cross_encoder.run --latency results/e3/cross_encoder.latency.tsv ^
    --out results/e3/cross_encoder ^
    --meta system="Cross-encoder" group=Reranker
```

Los datos de `--meta` los usan los gráficos:

- `system`: el nombre que saldrá en tablas y gráficos.
- `group`: `Retrieval`, `Reranker` o `Cascada` (da el color; máximo 3 grupos).
- `corpus_size`: solo para E6, el número de documentos del corpus de esa corrida.

## Pruebas de carga (E5 y E6)

`ResultWriter` es seguro con varios hilos, así que puedes lanzar consultas en paralelo y cada una registra su propia latencia:

```python
from concurrent.futures import ThreadPoolExecutor
rw = ResultWriter("results/e5/cascada_carga")
def una(qid, texto):
    with rw.request(qid) as r:
        r.set_results(mi_sistema(texto))
with ThreadPoolExecutor(8) as pool:
    for qid, texto in queries:
        pool.submit(una, qid, texto)
rw.close()
```

## Reglas para no chocar

- Usa **las mismas queries y los mismos splits** que el resto: ajusta en `dev`, reporta en `test`.
- Guarda **los 20 candidatos como mínimo**, ordenados por tu score (el ResultWriter guarda hasta 100 por defecto). MRR@10 y Hole@10 necesitan más de 3 documentos aunque el sistema devuelva solo 3.
- Para comparar base y propuesta, ambas corren sobre **los mismos candidatos y el mismo dataset de one-pagers** (`07-comparacion-arquitecturas.md`), y el run guarda los scores de todos los candidatos.
- Repite cada corrida de latencia varias veces: con pocas consultas el p99 es inestable.
- Cada resultado se reporta con P@3 **y** p99 juntos.
