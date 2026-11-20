"""Create and execute the post-run notebook on CPU, without rerunning inference."""
from pathlib import Path
import json,os,sys,time,hashlib
import numpy as np
import pandas as pd
import nbformat
from analyze_v4 import Run,dump

ROOT=Path(__file__).resolve().parent
run=Run(ROOT)
verification=run.verify()
notes=run.figures()
run.aggregate().to_csv(ROOT/'tabla_paper_trec-covid.csv',index=False)
run.fitness().to_csv(ROOT/'fitness_por_repeticion.csv',index=False)
run.hedging().to_csv(ROOT/'hedging_pareado.csv',index=False)
run.exposure().to_csv(ROOT/'hedging_exposicion_por_solicitud.csv',index=False)
reference_summary=pd.read_csv(ROOT/'reference_fiqa_summary.csv')
actual_loads=run.summary.pivot(index='rep',columns='condition',values='offered_qps').sort_index(axis=1)
reference_loads=reference_summary.pivot(index='rep',columns='condition',values='offered_qps').sort_index(axis=1)
assert actual_loads.index.equals(reference_loads.index) and actual_loads.columns.equals(reference_loads.columns)
loads_equal=bool(np.array_equal(actual_loads.to_numpy(),reference_loads.to_numpy()))
meta=run.meta; ref=json.loads((ROOT/'reference_fiqa_run_meta.json').read_text())
checks=dict(same_source=meta['script_sha256']==ref['script_sha256'],same_python=meta['python'].split()[0]==ref['python'].split()[0],
 same_libraries=meta['libraries']==ref['libraries'],same_node=meta['node']==ref['node']=='ds001',
 same_gpu_model='RTX A6000' in meta['nvidia_smi'] and 'RTX A6000' in ref['nvidia_smi'],
 same_frozen_config=meta['frozen_config']==ref['frozen_config'],same_alpha=meta['alpha_json']==ref['alpha_json'],
 same_threads=meta['args']['threads']==ref['args']['threads']==4,
 same_reps=meta['args']['reps']==ref['args']['reps']==3,
 same_cond_seconds=meta['args']['cond_seconds']==ref['args']['cond_seconds']==180,
 same_warmup=meta['args']['warmup_seconds']==ref['args']['warmup_seconds']==30,
 same_calib_queries=meta['args']['calib_queries']==ref['args']['calib_queries']==500,
 same_ramp_seconds=meta['args']['ramp_seconds']==ref['args']['ramp_seconds']==120,
 same_ramp_rates=meta['args']['ramp_rates']==ref['args']['ramp_rates']=='1,2,4,8,16,32,64',
 same_calibration_rule=False,same_absolute_loads_as_fiqa=loads_equal,gpu_contention_controlled=False,reference_minilm_revision_verified=False)
assert all(value for key,value in checks.items() if key not in ['gpu_contention_controlled','reference_minilm_revision_verified','same_calibration_rule'])
dump(ROOT/'comparability_final.json',dict(checks=checks,reference_job=ref['slurm_job_id'],new_job=meta['slurm_job_id'],
    protocol=run.cal['protocol'],trec_capacity_qps=None,limitations=json.loads((ROOT/'comparability_preflight.json').read_text())['limits']+['TREC failed original v4 capacity criterion; subsequent 8-QPS reference is an external fixed-load experiment, not a normalized TREC-capacity run']))
cells=[]
def md(s): cells.append(nbformat.v4.new_markdown_cell(s))
def code(s): cells.append(nbformat.v4.new_code_cell(s))
md('# Trabajo 3 de MINION en Khipu\n\nLatencia, continuidad y fallas con TREC-COVID, comparable por montaje nominal con FiQA v4. '
   'Esta ejecución usa corpus completo y no cambia α=0,85. La relevancia se evalúa en el Trabajo 1; aquí se miden tiempos y rutas de respuesta.')
md('## Qué queremos aprender\n\n'
   'Al aumentar la tasa de llegada, observamos la cola de latencia y las rutas de respaldo. '
   'Al inyectar fallas, comprobamos si la respuesta sigue entregando tres documentos dentro de 2500 ms. '
   'F3H y F3NH cambian la política de hedging con iguales llegadas y asignación determinista de demoras. Las demoras efectivas pueden diferir por respaldos antes del reranker; se audita esa exposición sin afirmar aislamiento causal perfecto. '
   'Las repeticiones describen la variación del montaje: mediana y rango no son intervalos de confianza.')
code("from pathlib import Path\nimport json,sys\nimport pandas as pd\nfrom IPython.display import display,Image,Markdown\nROOT=Path.cwd()\nsys.path.insert(0,str(ROOT))\nfrom analyze_v4 import Run\nrun=Run(ROOT)\nprint('Job experimental:',run.meta['slurm_job_id'],'| nodo:',run.meta['node'])\nprint('Job de análisis:',__import__('os').environ.get('SLURM_JOB_ID'))\nprint('Referencia externa de carga (NO capacidad TREC):',run.cal['C_qps'],'QPS | hedge:',run.cal['hedge_threshold_ms'],'ms')")
md('## Montaje y comparabilidad\n\n'
   'La referencia es FiQA v4, job 63828. Se mantienen código, configuración, α, Python, librerías, nodo ds001/A6000, '
   'un shard, 4 CPU, 32 GB, 3 repeticiones, 180 s por condición y 30 s de descarte. '
   'El protocolo original de capacidad falla en TREC. El ensayo complementario usa las mismas cargas absolutas de FiQA (2/4/6/8 QPS), conservando plazos y código; no constituye una comparación a C propia de TREC. '
   'La GPU es compartida: no se controla la misma contención que en la referencia. La revisión exacta de MiniLM no fue registrada por FiQA; se documenta la nueva revisión, sin afirmar una comprobación retrospectiva de pesos.')
code("comparison=json.loads((ROOT/'comparability_final.json').read_text())\ndisplay(pd.Series(comparison['checks']).to_frame('verificado'))\nprint('Python benchmark:',run.meta['python'].split()[0])\ndisplay(pd.Series(run.meta['libraries']).to_frame('versión'))\nprint('Hardware registrado:')\nprint(run.meta['nvidia_smi'])")
md('## Flujo de una solicitud\n\n'
   'El generador Poisson no espera la solicitud anterior. La latencia se cuenta desde el instante programado, incluyendo espera. '
   'BM25 y BGE corren en paralelo; se unen sus top 10, se completan ambos puntajes y se normaliza min-max por consulta. '
   'La fusión α=0,85 alimenta el reranker y sus dos réplicas comparten la A6000. '
   'Si una etapa falla o vence su plazo, se devuelve la ruta de respaldo correspondiente.\n\n'
   '```text\nPoisson open-loop → BM25 y BGE en paralelo → unión y fusión\n'
   ' → reranker A (hedge B si aplica) → respuesta o respaldo\n```')
md('## Datos y condiciones\n\n'
   'Se usan 171.332 documentos y las 50 consultas test. Las consultas de calibración son títulos de 1000 documentos elegidos con semilla 42; se envían 500 en la calibración a 1 QPS. '
   'FiQA usa consultas train como calibración. El test no se utiliza para elegir α ni umbrales de relevancia.')
code("display(Markdown((ROOT/'PLAN_EXPERIMENTAL.md').read_text()))\nprint('Argumentos ejecutados:')\ndisplay(pd.Series(run.meta['args']).to_frame('valor'))")
md('## Calibración separada por dataset\n\n'
   'El umbral de hedging es el p95 del reranker medido a 1 QPS. C exige al menos 99 % de respuestas de ruta completa reranked y estabilidad del p99. '
   'En v4, la primera falla limita C; el resto de la rampa se conserva como diagnóstico. '
   'La calibración original 63911 no pudo fijar C: la primera tasa falló. Los datos de 500 consultas se conservan, pero la fuente original solo dejó la rampa redondeada en el log. El umbral propio de hedging se reutiliza y la carga se fija externamente a partir de FiQA; no se cambia el 99 % ni se declara una capacidad de TREC.')
code("display(pd.DataFrame(run.cal['ramp_log_rounded']))\nprint('C TREC validada:',run.cal['trec_capacity_qps'])\nprint('Referencia externa de carga:',run.cal['C_qps'])")
for name in ['K1_rampa_trec-covid.png','K2_etapas_trec-covid.png']:
    md('### '+name.split('_')[0]+' Calibración')
    code(f"display(Image(filename=str(ROOT/'figs'/'{name}')))")
    md(notes[name])
md('## Carga y latencia\n\n'
   'L25–L100 son etiquetas heredadas del código: aquí representan 2/4/6/8 QPS, porcentajes de la referencia externa de FiQA, NO de una C validada para TREC. '
   'Los percentiles se calculan con ceil(q×N) sobre respuestas de tres documentos. La continuidad incluye todas las solicitudes medidas. '
   'Una latencia válida puede provenir de respaldo, por lo que también se debe mirar la distribución de rutas.')
code("display(run.aggregate())\nprint('Resultados individuales de las tres repeticiones:')\ndisplay(run.summary[['rep','condition','offered_qps','n_sent','p99_ms','continuity_pct','pct_dup']])")
for name in ['K3_ecdf_carga_trec-covid.png','K4_percentiles_carga_trec-covid.png','K5_serie_tiempo_trec-covid.png']:
    md('### '+name.split('_')[0]+' Carga')
    code(f"display(Image(filename=str(ROOT/'figs'/'{name}')))")
    md(notes[name])
md('## Fallas y rutas de respuesta\n\n'
   'NORERANK omite el modelo y es una referencia de costo temporal. F1/F2 sí intentan invocarlo y activan respaldo por error o timeout. '
   'F4/F5 conservan la ruta de recuperación disponible. F6 representa la pérdida de ambas rutas: se espera un error controlado, no continuidad.')
for name in ['K6_matriz_rutas_trec-covid.png','K7_continuidad_trec-covid.png']:
    code(f"display(Image(filename=str(ROOT/'figs'/'{name}')))")
    md(notes[name])
md('## Comparación pareada del hedging\n\n'
   'Se verifican IDs y horarios iguales y la asignación de demoras por semilla 42 e índice. Las banderas observadas se reportan aparte: si una consulta usa respaldo antes de rerank, no recibe la demora asignada a esa etapa. '
   'La reducción se define p99 sin hedge menos p99 con hedge; un valor negativo indica empeoramiento. '
   'Las diferencias entre tres p99 son descriptivas y no equivalen a un ensayo con solicitudes independientes.')
code("display(run.hedging())\ndisplay(Image(filename=str(ROOT/'figs'/'K8_hedging_trec-covid.png')))")
md(notes['K8_hedging_trec-covid.png'])
md('## Fitness y relación con el Trabajo 1\n\n'
   'Se comprueban p99 bajo carga, continuidad mínima en F1/F2 y duplicadas máximas en L25–L100/F3H. '
   'La mejora de P@3 se responde con la evaluación offline ya ejecutada: no se deriva de la continuidad. '
   'La misma lista de respaldo puede tener distinta calidad y distinto costo temporal.')
code("display(run.fitness())\ndisplay(Image(filename=str(ROOT/'figs'/'K9_fitness_trec-covid.png')))")
md(notes['K9_fitness_trec-covid.png'])
md('## FiQA y TREC-COVID en ds001\n\n'
   'La siguiente tabla mantiene los resultados de cada dataset separados e incluye C y QPS absolutos. '
   'No se atribuye una diferencia a la GPU porque ambos usan A6000, ni se atribuye causalmente al dataset sin controlar la contención compartida.')
code("reference=pd.read_csv(ROOT/'reference_fiqa_summary.csv')\nrefmeta=json.loads((ROOT/'reference_fiqa_run_meta.json').read_text())\nrows=[]\nfor ds,table,C in [('fiqa',reference,refmeta['calibration_json']['C_qps']),('trec-covid',run.summary,run.cal['C_qps'])]:\n    for c in ['L100','NORERANK','F1','F2','F3H','F3NH']:\n        g=table[table.condition==c]\n        rows.append(dict(dataset=ds,condition=c,C_qps=C if ds=='fiqa' else None,external_load_reference_qps=8,offered_qps=g.offered_qps.iloc[0],p99_median_ms=g.p99_ms.median(),p99_min_ms=g.p99_ms.min(),p99_max_ms=g.p99_ms.max(),continuity_min_pct=g.continuity_pct.min()))\ndisplay(pd.DataFrame(rows))")
md('## Interpretación y límites\n\n'
   'El sistema es un proceso con hilos y dos réplicas en una GPU compartida; las fallas son inyectadas y no representan máquinas físicamente independientes. '
   'Las consultas test se recorren cíclicamente: más solicitudes no equivalen a nuevas consultas independientes. '
   'Las comparaciones estadísticas de relevancia y los análisis de invocación no sustituyen mediciones temporales de esas variantes.')
code("a=run.aggregate().set_index('condition')\nh=run.hedging()\nf=run.fitness()\nprint('p99 L100 mediana [mínimo,máximo]:',a.loc['L100',['p99_ms_median','p99_ms_min','p99_ms_max']].to_dict())\nprint('Reducciones p99 por hedge:',h.p99_reduction_ms.tolist())\nprint('Repeticiones que cumplen i, iii, iv:',f[['fitness_i','fitness_iii','fitness_iv']].sum().to_dict())\nprint('Fuente exacta del benchmark:',run.meta['script_sha256'])\nprint('Conclusiones limitadas a este montaje y la contención registrada.')")
md('## Verificación final y archivos\n\n'
   'Los percentiles, continuidad y porcentaje de duplicadas se contrastan contra cada archivo de solicitudes después del descarte. '
   'El intento de capacidad, el piloto y el ensayo a carga fija permanecen separados. Este notebook solo relee resultados: no repite inferencia. El campo C_qps=8 del adaptador de entrada solo escala cargas y NO valida la capacidad de TREC.')
code("verification=run.verify()\nassert verification['passed']\nassert len(list((ROOT/'figs').glob('*.png')))==9\nprint('39 condiciones verificadas; tres pares de IDs y horarios iguales, exposición a demoras auditada; nueve figuras.')")
spec=ROOT/'analysis_runtime/kernels/minion-v4'; spec.mkdir(parents=True,exist_ok=True)
dump(spec/'kernel.json',dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Python análisis MINION',language='python'))
os.environ['JUPYTER_PATH']=str(ROOT/'analysis_runtime')
nb=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'minion-v4','language':'python','display_name':'Python análisis MINION'}})
from nbclient import NotebookClient
path=ROOT/'trabajo3_latencia_trec_covid_khipu.ipynb'
try:
    NotebookClient(nb,timeout=600,kernel_name='minion-v4',allow_errors=False,resources={'metadata':{'path':str(ROOT)}}).execute()
finally: nbformat.write(nb,path)
codes=[c for c in nb.cells if c.cell_type=='code']
assert all(c.execution_count is not None for c in codes)
assert not [o for c in codes for o in c.outputs if o.output_type=='error']
assert sum('image/png' in o.get('data',{}) for c in codes for o in c.outputs)==9
dump(ROOT/'analysis_summary.json',dict(passed=True,notebook_code_cells=len(codes),notebook_errors=0,figures=9,
    protocol=run.cal['protocol'],capacity_validated=False,trec_capacity_qps=None,experimental_job=meta['slurm_job_id'],analysis_job=os.environ.get('SLURM_JOB_ID'),
    benchmark_source_sha256=meta['script_sha256'],notebook_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
print('ANALYSIS_NOTEBOOK_COMPLETE_VERIFIED',flush=True)
