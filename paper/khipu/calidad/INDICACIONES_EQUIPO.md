# Indicaciones para correr la comparación base vs propuesta

Rama: `feat/calidad-comparacion`. Código en `paper/khipu/calidad/` y `paper/khipu/kaggle-calidad/`.

## Qué se va a correr

Se compara la arquitectura **base** (BM25 + embeddings) con la **propuesta** (BM25 + un LLM pequeño que puntúa cada documento), sobre FiQA con una submuestra de **8.000 documentos**. Los dos usan los mismos candidatos, y el score del LLM es un número continuo entre 0 y 1. El detalle está en `paper/khipu/calidad/README.md`.

Cada uno corre su propia versión completa, en Kaggle o en Khipu, como prefiera. Si una falla, quedan las otras de respaldo. La primera que termine bien es la oficial y las demás son réplicas.

> Nada se ha probado todavía con datos ni modelos reales. Por eso el paso 2 es una prueba corta antes de la corrida completa.

## 1. Preparar y comprobar el código (2 minutos, sin GPU)

```
git fetch
git checkout feat/calidad-comparacion
cd paper/khipu/calidad
pip install -r requirements.txt
python -m pytest tests -q
```

Tienen que salir **60 pruebas pasadas**. Si falla alguna, copien el error completo y avisen en el grupo.

## 2. Prueba corta (10 a 20 minutos)

Usa 64 documentos y 20 consultas. **Los números de esta prueba no sirven**: solo comprueba que todo encadena.

**Kaggle**
1. Desde `paper/khipu`, corran `bash kaggle-calidad/preparar_dataset.sh`.
2. Suban el resultado como dataset `minion-calidad`: `kaggle datasets create -p kaggle-calidad/dataset --dir-mode zip`. También hace falta el dataset `minion-bench`, que ya existe.
3. En `kaggle-calidad/dataset-metadata.json` y `kaggle-calidad/kernel-metadata.json`, cambien `gianpiersegoviaureta` por su usuario de Kaggle.
4. Dejen `SMOKE = True` en `kaggle-calidad/runner.py`.
5. Lancen: `kaggle kernels push -p kaggle-calidad`, con GPU e internet activados.

**Khipu**
1. En el nodo de acceso (tiene internet): `bash calidad/khipu_preparar.sh`.
2. Lancen: `sbatch calidad/khipu_correr.sbatch` (por defecto es la prueba corta).

Ojo: los scripts de Khipu **no están probados** en el clúster. Revisen la partición y la GPU con `sinfo` y `myaccount` antes de lanzar.

## 3. Corrida completa (unas 3 a 4 horas)

El tiempo es un estimado, no está medido. Solo se lanza si la prueba corta terminó bien.

- **Kaggle:** pongan `SMOKE = False` en `runner.py` y vuelvan a lanzar.
- **Khipu:** `SMOKE=0 sbatch calidad/khipu_correr.sbatch`.

El modelo se elige solo: prueba `Qwen/Qwen2.5-3B-Instruct` y, si falla en esa GPU, usa `Qwen/Qwen2.5-1.5B-Instruct`. Si el kernel se corta, vuelvan a lanzar: retoma donde quedó.

## 4. Qué deja la corrida (cada uno genera su propio reporte)

Al terminar, el pipeline arma solo el reporte. No hace falta mandarle nada a nadie para que se genere. Quedan en `calidad_out/reporte/`:

- `reporte.md`: tabla de las tres arquitecturas (solo léxico, base y propuesta), la diferencia propuesta menos base con su intervalo de confianza, la latencia del sLLM con batch 4 y batch 10, el porcentaje de scores degradados y los límites del experimento.
- Cuatro gráficos (`fig1` a `fig4`): calidad por arquitectura, peso del léxico, latencia por batch y reparto de los scores del sLLM.

Antes de dar por buena la corrida, revisen en `reporte.md`:
- Que no diga **"prueba corta"** arriba (si lo dice, fue la corrida con `SMOKE`).
- Que el **% de degradadas** sea bajo y que la diferencia máxima entre batches sea casi 0.
- Que el porcentaje de scores "exactamente 0 o 1" no sea muy alto.

Guarden también `calidad_out/` entero o `calidad_results.tar.gz`. **En Khipu, cópienlo fuera del clúster**, porque no hay backup. Si algo falló, `calidad_out/pasos.json` muestra hasta qué paso llegó. Y para escribir el paper, cada quien decide qué números y gráficos usar de su reporte.

## 5. Cuidados

- No suban `paper/.kaggle`: tiene el token de Kaggle.
- No usen `git add .`. Agreguen solo los archivos que cambien a propósito.
- No toquen `minion_bench.py` ni `alpha.json`.
- No usen la misma cuenta de Kaggle dos personas a la vez, para no gastar la cuota de GPU de la otra.
- Para que las latencias sean comparables con las del equipo, la GPU debe ser la T4 de Kaggle. La calidad (P@3) casi no depende de la GPU.

## Si algo falla

| Qué pasa | Qué hacer |
|---|---|
| Fallan las pruebas del paso 1 | Copien el error completo y avisen en el grupo. |
| El paso "verificar modelos" no deja ninguno | Revisen `calidad_out/modelos_ok.json`; ahí dice por qué falló cada modelo. |
| Se acaba la memoria de la GPU | El código parte el batch solo; si aun así falla, copien el log y avisen en el grupo. |
| El kernel se corta a mitad | Vuelvan a lanzar: se salta lo ya hecho. |
| Khipu rechaza el script | Revisen partición y GPU (`sinfo`, `myaccount`) y avisen en el grupo con el error. |
