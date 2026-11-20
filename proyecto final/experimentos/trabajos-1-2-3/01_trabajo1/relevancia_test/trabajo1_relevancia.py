# %% [markdown]
# # MINION — relevancia offline: fusión y reranking
# 
# Evaluación final de **FiQA-test** y **TREC-COVID-test**, ejecutada en Khipu mediante Slurm. **α = 0,85** fue fijado en FiQA-dev y no se vuelve a ajustar. El corpus y los juicios se conservan tal como fueron publicados; no se entrenan modelos ni se seleccionan configuraciones con test.

# %% [markdown]
# ## 0. Resumen ejecutivo
# 
# - **fiqa:** P@3 fused 0.2515; reranked 0.2310; Δ -0.0206, IC 95 % [-0.0355, -0.0057].
# - **trec-covid:** P@3 fused 0.9133; reranked 0.8867; Δ -0.0267, IC 95 % [-0.0933, +0.0333].
# - La diferencia compara los mismos candidatos por consulta; solo cambia su orden.
# - Los IC usan 10.000 remuestreos pareados de consultas, semilla 42.
# - La cobertura de juicios y el resultado condensado se reportan como análisis de sensibilidad.

# %% [markdown]
# ## 1. Objetivo, protocolo y reproducibilidad
# 
# Se pregunta si un cross-encoder mejora la relevancia del top 3 de la fusión híbrida. Una unidad de evaluación es una consulta; las métricas son promedios macro por consulta. El módulo `minion_test.py` acompaña este notebook y contiene los cálculos usados por los jobs. Las etapas costosas tienen caché: al reejecutar se verifican y reutilizan los puntajes ya calculados.

# %%
import os, sys, json, time, gc
from pathlib import Path
import pandas as pd
from IPython.display import display, Image, Markdown
ROOT = Path(os.environ.get('MINION_ROOT', str(Path.cwd().parent))).resolve()
OUT = ROOT / 'test_results'
sys.path.insert(0, str(ROOT))
from minion_test import load_dataset, retrieve, rerank, evaluate, sha
alpha = json.loads((OUT / 'alpha_usado.json').read_text())
assert alpha['alpha'] == 0.85 and not alpha['pilot']
assert sha(OUT / 'alpha_usado.json') == sha(ROOT / 'results/alpha.json')
ctx = dict(root=ROOT, out=OUT, pilot=False, alpha=alpha, started=time.monotonic(),
    summary=json.loads((OUT / 'run_summary.json').read_text()))
print('Python:', sys.executable)
print('α:', alpha['alpha'], '| revisión BGE:', alpha['model_revision'])
print('Job de cómputo:', ctx['summary']['job_id'], '| nodo:', ctx['summary']['node'])

# %% [markdown]
# ### Configuración congelada y desempates
# 
# BM25 usa bm25s/lucene, k1=0,9, b=0,4, stopwords inglesas y PyStemmer english. BGE usa el prefijo especificado solo en consultas, CLS, forward fp16, normalización L2 en float32 y longitud máxima 512. Se busca con `faiss.IndexFlatIP`; los empates se resuelven por ID ascendente, incluso en el corte del top 10. El cross-encoder usa float32 y procesa todos los candidatos de una consulta en un lote. Sus empates conservan el orden fusionado. Los runs TREC usan puntajes monotónicos derivados del rango para conservar ese orden; los puntajes originales se guardan en parquet.

# %%
display(pd.DataFrame([alpha['bm25']]))
display(pd.DataFrame([alpha['semantic']]))
print('Normalización:', alpha['normalization'])
print('Desempate:', alpha['document_tie_break'])
print('Reranker:', ctx['summary']['reranker'])

# %% [markdown]
# ## 2. Datos, auditoría y separación desarrollo/prueba
# 
# FiQA contiene preguntas y pasajes financieros; TREC-COVID contiene consultas y artículos científicos sobre COVID-19. Se comprueban los conteos de ambos corpus y sus consultas de prueba; los qrels se usan solo para evaluar. No se eliminan textos vacíos ni duplicados: el corpus publicado queda intacto. TREC-COVID incluye dos entradas −1; `trec_eval` las interpreta como sin juicio. La métrica nDCG conserva los grados originales 0, 1 y 2 y el evaluador da ganancia cero a −1. [Convención oficial NIST](https://github.com/usnistgov/trec_eval/blob/main/formats.c).

# %%
counts = json.loads((OUT / 'counts.json').read_text())
display(pd.DataFrame(counts).T)
assert counts['fiqa']['corpus'] == 57638 and counts['fiqa']['test_queries'] == 648
assert counts['trec-covid']['corpus'] == 171332 and counts['trec-covid']['test_queries'] == 50

# %% [markdown]
# ## 3. FiQA-test: recuperación y fusión
# 
# Se lee el corpus completo con texto `title + " " + text`. Solo se usan consultas del split test. La siguiente celda comprueba los datos y muestra un ejemplo real.

# %%
state = load_dataset(ctx, 'fiqa')
q = state['qids'][0]
print('Consulta:', q, state['queries'][q])
print('Documento de ejemplo:', state['docs'][0]['_id'], state['texts'][0][:500])

# %% [markdown]
# ### Índice BM25, embeddings y candidatos
# 
# Se reutilizan índices y embeddings compatibles. Para cada consulta se unen top 10 BM25 y top 10 denso por ID. Se calculan ambos puntajes de todos los candidatos, incluso cuando un documento llegó por una sola ruta. La normalización min-max se aplica dentro de esta unión; si el vector es constante se asigna 1. La fusión es `(1 − 0,85) × lex_norm + 0,85 × sem_norm`.

# %%
candidates = retrieve(ctx, state)
assert candidates.groupby('query_id').size().between(10,20).all()
print('Candidatos:', len(candidates), '| consultas:', candidates.query_id.nunique())
display(candidates.head())

# %% [markdown]
# ### Cross-encoder sobre exactamente los mismos documentos
# 
# MiniLM puntúa los pares consulta-documento; no agrega ni elimina candidatos. Se guarda su puntaje original junto con los puntajes de recuperación. El caché permite ejecutar el notebook sin repetir inferencias ya terminadas.

# %%
runs = rerank(ctx, state)
assert all(set(runs['fused'][q]) == set(runs['reranked'][q]) for q in state['qids'])
print('Igualdad de candidatos verificada en todas las consultas.')

# %% [markdown]
# ### Métricas, contraste independiente y bootstrap pareado
# 
# Se calculan P(rel≥1)@3, nDCG@3 y RR(rel≥1)@10 con `ir_measures`. Recall@20 se reporta solo para fused y promedia consultas con al menos un relevante. Un segundo cálculo explícito por consulta debe coincidir con el evaluador. Cada remuestreo usa los mismos IDs de consultas para fused y reranked; se reinicia `default_rng(42)` por dataset.

# %%
comparison = evaluate(ctx, state)
display(pd.read_csv(OUT / 'metrics.csv').query("dataset == 'fiqa'"))
display(pd.DataFrame([comparison]))
del state, candidates, runs
gc.collect()

# %% [markdown]
# ## 3. TREC-COVID-test: recuperación y fusión
# 
# Se lee el corpus completo con texto `title + " " + text`. Solo se usan consultas del split test. La siguiente celda comprueba los datos y muestra un ejemplo real.

# %%
state = load_dataset(ctx, 'trec-covid')
q = state['qids'][0]
print('Consulta:', q, state['queries'][q])
print('Documento de ejemplo:', state['docs'][0]['_id'], state['texts'][0][:500])

# %% [markdown]
# ### Índice BM25, embeddings y candidatos
# 
# Se reutilizan índices y embeddings compatibles. Para cada consulta se unen top 10 BM25 y top 10 denso por ID. Se calculan ambos puntajes de todos los candidatos, incluso cuando un documento llegó por una sola ruta. La normalización min-max se aplica dentro de esta unión; si el vector es constante se asigna 1. La fusión es `(1 − 0,85) × lex_norm + 0,85 × sem_norm`.

# %%
candidates = retrieve(ctx, state)
assert candidates.groupby('query_id').size().between(10,20).all()
print('Candidatos:', len(candidates), '| consultas:', candidates.query_id.nunique())
display(candidates.head())

# %% [markdown]
# ### Cross-encoder sobre exactamente los mismos documentos
# 
# MiniLM puntúa los pares consulta-documento; no agrega ni elimina candidatos. Se guarda su puntaje original junto con los puntajes de recuperación. El caché permite ejecutar el notebook sin repetir inferencias ya terminadas.

# %%
runs = rerank(ctx, state)
assert all(set(runs['fused'][q]) == set(runs['reranked'][q]) for q in state['qids'])
print('Igualdad de candidatos verificada en todas las consultas.')

# %% [markdown]
# ### Métricas, contraste independiente y bootstrap pareado
# 
# Se calculan P(rel≥1)@3, nDCG@3 y RR(rel≥1)@10 con `ir_measures`. Recall@20 se reporta solo para fused y promedia consultas con al menos un relevante. Un segundo cálculo explícito por consulta debe coincidir con el evaluador. Cada remuestreo usa los mismos IDs de consultas para fused y reranked; se reinicia `default_rng(42)` por dataset.

# %%
comparison = evaluate(ctx, state)
display(pd.read_csv(OUT / 'metrics.csv').query("dataset == 'trec-covid'"))
display(pd.DataFrame([comparison]))
del state, candidates, runs
gc.collect()

# %% [markdown]
# ## 4. Resultados visuales
# 
# Todas las figuras fueron generadas con matplotlib y guardadas como PNG a 200 dpi. Los colores siguen Okabe–Ito. Los intervalos R1 son marginales; R2 presenta la diferencia pareada.

# %% [markdown]
# ### R3 alpha fiqa dev

# %%
display(Image(filename=str(OUT / 'figs' / 'R3_alpha_fiqa_dev.png')))

# %% [markdown]
# La curva proviene del archivo validado de desarrollo: no se recalculó ni se usó test para ajustar α.
# El valor fijo 0,85 se aplica sin cambios a FiQA-test y TREC-COVID.

# %% [markdown]
# ### R1 metricas fiqa

# %%
display(Image(filename=str(OUT / 'figs' / 'R1_metricas_fiqa.png')))

# %% [markdown]
# P@3 pasa de 0.2515 (fusión) a 0.2310 (reranking).
# Las barras muestran IC marginales; la comparación pareada de ΔP@3 está en R2. MRR de lex y sem es complementario.

# %% [markdown]
# ### R2 bootstrap fiqa

# %%
display(Image(filename=str(OUT / 'figs' / 'R2_bootstrap_fiqa.png')))

# %% [markdown]
# ΔP@3 = -0.0206; IC 95 % [-0.0355, -0.0057].
# El intervalo es negativo; el remuestreo conserva el emparejamiento por consulta.

# %% [markdown]
# ### R4 matriz transicion fiqa

# %%
display(Image(filename=str(OUT / 'figs' / 'R4_matriz_transicion_fiqa.png')))

# %% [markdown]
# 72 consultas mejoran, 470 empatan y 106 empeoran.
# Las celdas a la derecha y por encima de la diagonal representan mejoras; la diagonal representa empates.

# %% [markdown]
# ### R5 gana empata pierde fiqa

# %%
display(Image(filename=str(OUT / 'figs' / 'R5_gana_empata_pierde_fiqa.png')))

# %% [markdown]
# El reranker mejora 11.1 %, empata 72.5 % y empeora 16.4 % de las consultas.
# El cambio promedio debe interpretarse junto con estas diferencias entre consultas.

# %% [markdown]
# ### R6 matriz posiciones fiqa

# %%
display(Image(filename=str(OUT / 'figs' / 'R6_matriz_posiciones_fiqa.png')))

# %% [markdown]
# 97 relevantes entran al top 3 desde posiciones inferiores; 137 salen del top 3.
# Cada documento es el mismo antes y después: esta figura aísla el efecto de reordenar candidatos.

# %% [markdown]
# ### R7 origen candidatos fiqa

# %%
display(Image(filename=str(OUT / 'figs' / 'R7_origen_candidatos_fiqa.png')))

# %% [markdown]
# La unión contiene 18.00 candidatos por consulta y 1.23 relevantes juzgados.
# Los aportes relevantes exclusivos de BM25 y denso son 0.11 y 0.58 por consulta.

# %% [markdown]
# ### R8 judged fiqa

# %%
display(Image(filename=str(OUT / 'figs' / 'R8_judged_fiqa.png')))

# %% [markdown]
# Judged@10: fusión 11.6 %, reranker 10.6 %. Los grados 0 cuentan como juzgados.
# ΔP@3 condensada = +0.0000; cambia el signo respecto de la evaluación original. FiQA solo tiene juicios positivos: el empate de P@3 condensada es estructural al compartir candidatos.

# %% [markdown]
# ### R1 metricas trec-covid

# %%
display(Image(filename=str(OUT / 'figs' / 'R1_metricas_trec-covid.png')))

# %% [markdown]
# P@3 pasa de 0.9133 (fusión) a 0.8867 (reranking).
# Las barras muestran IC marginales; la comparación pareada de ΔP@3 está en R2. MRR de lex y sem es complementario.

# %% [markdown]
# ### R2 bootstrap trec-covid

# %%
display(Image(filename=str(OUT / 'figs' / 'R2_bootstrap_trec-covid.png')))

# %% [markdown]
# ΔP@3 = -0.0267; IC 95 % [-0.0933, +0.0333].
# El intervalo es compatible con cero; el remuestreo conserva el emparejamiento por consulta.

# %% [markdown]
# ### R4 matriz transicion trec-covid

# %%
display(Image(filename=str(OUT / 'figs' / 'R4_matriz_transicion_trec-covid.png')))

# %% [markdown]
# 6 consultas mejoran, 37 empatan y 7 empeoran.
# Las celdas a la derecha y por encima de la diagonal representan mejoras; la diagonal representa empates.

# %% [markdown]
# ### R5 gana empata pierde trec-covid

# %%
display(Image(filename=str(OUT / 'figs' / 'R5_gana_empata_pierde_trec-covid.png')))

# %% [markdown]
# El reranker mejora 12.0 %, empata 74.0 % y empeora 14.0 % de las consultas.
# El cambio promedio debe interpretarse junto con estas diferencias entre consultas.

# %% [markdown]
# ### R6 matriz posiciones trec-covid

# %%
display(Image(filename=str(OUT / 'figs' / 'R6_matriz_posiciones_trec-covid.png')))

# %% [markdown]
# 83 relevantes entran al top 3 desde posiciones inferiores; 87 salen del top 3.
# Cada documento es el mismo antes y después: esta figura aísla el efecto de reordenar candidatos.

# %% [markdown]
# ### R7 origen candidatos trec-covid

# %%
display(Image(filename=str(OUT / 'figs' / 'R7_origen_candidatos_trec-covid.png')))

# %% [markdown]
# La unión contiene 18.60 candidatos por consulta y 13.34 relevantes juzgados.
# Los aportes relevantes exclusivos de BM25 y denso son 5.06 y 6.98 por consulta.

# %% [markdown]
# ### R8 judged trec-covid

# %%
display(Image(filename=str(OUT / 'figs' / 'R8_judged_trec-covid.png')))

# %% [markdown]
# Judged@10: fusión 93.8 %, reranker 96.8 %. Los grados 0 cuentan como juzgados.
# ΔP@3 condensada = -0.0267; se mantiene el signo respecto de la evaluación original.

# %% [markdown]
# ## 5. Juicios faltantes y ejemplos
# 
# Judged@10 sigue literalmente la presencia del par consulta-documento en los qrels, incluido grado 0. La lista condensada elimina documentos cuyo par no aparece en qrels antes de calcular las métricas. Las dos entradas −1 se conservan y se audita si fueron recuperadas; no se alteran las etiquetas. La condensación de estas listas cortas es un análisis de sensibilidad, no una estimación de relevancia completa. FiQA solo tiene qrels positivos: al condensar se eliminan todos los negativos no juzgados y P@3 queda determinada por el número de relevantes en los mismos candidatos, por lo que la diferencia se fuerza a cero. Esto no demuestra ausencia de sesgo.

# %%
display(pd.read_csv(OUT / 'judged.csv'))
display(pd.read_csv(OUT / 'condensed.csv'))
display(Markdown((OUT / 'R9_ejemplos.md').read_text()))

# %% [markdown]
# ## 6. Tabla para el paper y rutas de respaldo
# 
# Si falla el reranker, la ruta de respaldo es fused; si falla la ruta semántica, lex; si falla la ruta léxica, sem. La tabla incluye relevancia, incertidumbre y cobertura de juicios. Estos resultados no miden latencia ni verifican un SLO.

# %%
display(pd.read_csv(OUT / 'paper_table.csv').T)
print('Run files:', sorted(p.name for p in (OUT / 'runs').glob('*.trec')))

# %% [markdown]
# ## 7. Conclusión y limitaciones
# 
# - En **fiqa**, el cross-encoder empeora P@3 en promedio: Δ = -0.0206 (-2.06 puntos porcentuales).
# - Su IC pareado 95 % [-0.0355, -0.0057] excluye cero; la Δ condensada es +0.0000 y el signo cambia. El empate condensado es estructural porque FiQA solo contiene juicios positivos.
# - En **trec-covid**, el cross-encoder empeora P@3 en promedio: Δ = -0.0267 (-2.67 puntos porcentuales).
# - Su IC pareado 95 % [-0.0933, +0.0333] incluye cero; la Δ condensada es -0.0267 y el signo se mantiene.
# - Se aplicó el mismo α=0,85 a ambos tests, sin selección de hiperparámetros sobre prueba.
# - El reranker únicamente reordena: no puede rescatar relevantes ausentes de la unión de candidatos.
# - Los juicios incompletos, los textos truncados a 512 tokens y la transferencia del modelo a dominios distintos limitan la interpretación.
# - El resultado es una evaluación de relevancia offline; no demuestra una mejora bajo un presupuesto de latencia.

# %% [markdown]
# ## 8. Procedencia y archivos
# 
# Se adjuntan el script de evaluación, el generador de figuras, los runs TREC, los puntajes parquet, los datos por consulta, las muestras bootstrap y la contabilidad Slurm. El α validado se copia byte por byte; la curva de desarrollo solo se visualiza.

# %%
print('α SHA-256:', sha(OUT / 'alpha_usado.json'))
print('Candidatos SHA-256:')
for ds in ['fiqa','trec-covid']:
    print(ds, sha(OUT / f'cands_{ds}_test.parquet'))
assert len(list((OUT / 'figs').glob('*.png'))) == 15
assert len(pd.read_csv(OUT / 'bootstrap.csv')) == 2
print('Verificación del notebook completada.')
