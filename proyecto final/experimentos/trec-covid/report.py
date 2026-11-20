"""CPU analysis of saved observations; executes a notebook and packages artifacts."""
from pathlib import Path
import csv, hashlib, json, os, subprocess, sys, time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'resultados'
OUT.mkdir(exist_ok=True)
def frame(name):
 p=OUT/name
 return pd.read_csv(p) if p.exists() and p.stat().st_size else pd.DataFrame()
def dump(name,obj):base.dump(OUT/name,obj)

def analyze():
 quality=frame('calidad_por_consulta.csv');lines=['# Comparación de fusión convexa y puntuación LLM',
  '', 'Análisis exploratorio de TREC-COVID sobre un corpus aleatorio de 10.000 documentos. Solo cambia la etapa final de ranking.']
 complete=(OUT/'calidad_completa.json').exists()
 lines+=['',f'**Calidad completa:** {complete}. Una tabla parcial no equivale a una evaluación final.']
 for stage in ['quality','performance']:
  p=OUT/f'entorno_{stage}.json'
  if p.exists():
   e=json.loads(p.read_text());lines+=['',f"{stage}: job {e['job']}, nodo {e['node']}, GPU {e['gpu']}, precisión LLM {e['precision_llm']}."]
  failure=OUT/f'fallo_{stage}.json'
  if failure.exists():lines+=['',f"**Fallo registrado en {stage}:** `{json.loads(failure.read_text())['error']}`"]
 summary=pd.DataFrame();ci=pd.DataFrame()
 if not quality.empty:
  assert not quality.duplicated(['qid','method']).any()
  assert np.isfinite(quality[['P3','nDCG3','MRR10']].to_numpy()).all()
  if complete:
   protocol=json.loads((OUT/'protocolo.json').read_text());nq=protocol['queries']
   assert len(quality)==4*nq and quality.qid.nunique()==nq
  summary=quality.groupby('method')[['P3','nDCG3','MRR10']].mean().reset_index()
  summary.to_csv(OUT/'calidad_resumen.csv',index=False)
  rng=np.random.default_rng(42);cirows=[]
  for metric in ['P3','nDCG3','MRR10']:
   pivot=quality.pivot(index='qid',columns='method',values=metric).dropna(subset=['LLM','fusion'])
   delta=(pivot.LLM-pivot.fusion).to_numpy();n=len(delta)
   assert n>0
   dist=delta[rng.integers(0,n,size=(10000,n))].mean(axis=1)
   lo,hi=np.quantile(dist,[.025,.975])
   cirows.append(dict(metric=metric,queries=n,difference_LLM_minus_fusion=float(delta.mean()),ci95_low=lo,ci95_high=hi,
    wins=int((delta>0).sum()),ties=int((delta==0).sum()),losses=int((delta<0).sum()),bootstrap_replicates=10000,seed=42))
  ci=pd.DataFrame(cirows);ci.to_csv(OUT/'diferencias_pareadas.csv',index=False)
  coverage=frame('cobertura_qrels.csv');positive=set(coverage.loc[coverage.positive_in_subset>0,'qid'])
  restricted=quality[quality.qid.isin(positive)]
  restricted.groupby('method')[['P3','nDCG3','MRR10']].mean().to_csv(OUT/'calidad_solo_consultas_con_positivos.csv')
  lines+=['','## Relevancia','',summary.to_markdown(index=False),'',ci.to_markdown(index=False),
   '',f'Consultas con al menos un positivo juzgado en la muestra: {len(positive)}/{coverage.shape[0]}. Las métricas principales conservan todas las consultas.']
  raw=json.loads((OUT/'scores_llm.json').read_text())
  assert all(np.isfinite(r['score']) and 0<=r['score']<=1 for r in raw)
  qualitygate=dict(pairs=len(raw),invalid_scores=0,degraded_label_mass_fraction=sum(r['degraded'] for r in raw)/len(raw),
   truncation_fraction=sum(r['truncated'] for r in raw)/len(raw),score_zero_or_one_fraction=sum(r['score'] in [0,1] for r in raw)/len(raw))
  dump('diagnostico_scores.json',qualitygate)
  lines+=['',f'Diagnóstico de puntuación: `{json.dumps(qualitygate)}`. Una masa baja en las etiquetas limita la interpretación del score condicional.']
  fig,ax=plt.subplots(figsize=(8,4));summary.set_index('method').plot.bar(ax=ax,rot=0)
  ax.set_ylim(0,1);ax.set_ylabel('Métrica media');ax.set_title('Calidad sobre los mismos candidatos');fig.tight_layout();fig.savefig(OUT/'fig1_calidad.png',dpi=160);plt.close(fig)
  fig,ax=plt.subplots(figsize=(7,4));x=np.arange(len(ci));d=ci.difference_LLM_minus_fusion.to_numpy()
  ax.errorbar(x,d,yerr=np.array([d-ci.ci95_low.to_numpy(),ci.ci95_high.to_numpy()-d]),fmt='o',capsize=5)
  ax.axhline(0,color='gray');ax.set_xticks(x,ci.metric);ax.set_ylabel('LLM menos fusión, IC 95 %');fig.tight_layout();fig.savefig(OUT/'fig2_diferencias.png',dpi=160);plt.close(fig)
 batch=frame('batches.csv')
 if not batch.empty:
  ok=batch[batch.status=='ok'];bsummary=ok.groupby('batch').agg(median_pairs_per_second=('pairs_per_second','median'),median_seconds=('seconds','median'),successful_repeats=('status','size')).reset_index()
  bsummary.to_csv(OUT/'batches_resumen.csv',index=False)
  stability=frame('estabilidad_batches.csv')
  lines+=['','## Batch y estabilidad','',bsummary.to_markdown(index=False),'',stability.to_markdown(index=False) if not stability.empty else 'Verificación de estabilidad no completada.']
  if not bsummary.empty:
   fig,ax=plt.subplots(figsize=(7,4));ax.bar(bsummary.batch.astype(str),bsummary.median_pairs_per_second)
   ax.set_xlabel('Tamaño de batch');ax.set_ylabel('Pares por segundo, mediana');fig.tight_layout();fig.savefig(OUT/'fig3_batches.png',dpi=160);plt.close(fig)
 concurrency=frame('concurrencia_resumen.csv')
 if not concurrency.empty:
  requests=frame('concurrencia_solicitudes.csv');quantiles=[]
  for level,g in requests[requests.status=='ok'].groupby('concurrency'):
   quantiles.append(dict(concurrency=level,successful_requests=len(g),p50_seconds=g.seconds.quantile(.5),
    p95_seconds=g.seconds.quantile(.95),p99_seconds=g.seconds.quantile(.99),p99_exploratory=len(g)<1000))
  pd.DataFrame(quantiles).to_csv(OUT/'concurrencia_percentiles.csv',index=False)
  lines+=['','## Concurrencia','',concurrency.to_markdown(index=False),
   '', 'Carga cerrada con una instancia de modelo y acceso GPU serializado; incluye espera interna. No demuestra capacidad con llegadas abiertas ni un óptimo universal.']
  fig,ax=plt.subplots(figsize=(7,4));c=concurrency.sort_values('concurrency');ax.plot(c.concurrency,c.successful_requests_per_second,'o-')
  ax.set_xlabel('Consultas simultáneas');ax.set_ylabel('Solicitudes correctas por segundo');fig.tight_layout();fig.savefig(OUT/'fig4_concurrencia.png',dpi=160);plt.close(fig)
 latency=frame('latencia_solicitudes.csv');tails=pd.DataFrame()
 if not latency.empty:
  rows=[]
  for method,allrows in latency.groupby('method'):
   ok=allrows[allrows.status=='ok'];v=ok.seconds.to_numpy()
   if not len(v):continue
   rows.append(dict(method=method,requests=len(allrows),successful=len(ok),errors=int((allrows.status!='ok').sum()),
    p50_seconds=float(np.quantile(v,.5)),p95_seconds=float(np.quantile(v,.95)),p99_seconds=float(np.quantile(v,.99)),
    mean_seconds=float(v.mean()),p99_exploratory=len(v)<1000))
  tails=pd.DataFrame(rows);tails.to_csv(OUT/'latencia_resumen.csv',index=False)
  lines+=['','## Latencia completa','',tails.to_markdown(index=False),
   '', 'Los percentiles corresponden a solicitudes correctas; los errores se informan por separado. Consultas repetidas, modelos calientes y sin caché de respuestas. p99 es especialmente incierto con pocas observaciones.']
  pivot=latency[latency.status=='ok'].pivot(index=['request','qid'],columns='method',values='seconds').dropna()
  if {'LLM','fusion'}.issubset(pivot.columns) and len(pivot):
   pivot['difference_seconds']=pivot.LLM-pivot.fusion;pivot['ratio_LLM_over_fusion']=pivot.LLM/pivot.fusion
   pivot.to_csv(OUT/'latencia_diferencias_pareadas.csv')
   lines+=['',f'Coste adicional medio en {len(pivot)} solicitudes pareadas: {pivot.difference_seconds.mean():.4f} s.']
  fig,ax=plt.subplots(figsize=(8,4));tails.set_index('method')[['p50_seconds','p95_seconds','p99_seconds']].plot.bar(ax=ax,rot=0)
  ax.set_ylabel('Segundos');fig.tight_layout();fig.savefig(OUT/'fig5_latencia.png',dpi=160);plt.close(fig)
 recovery=OUT/'recuperacion.json'
 if recovery.exists():lines+=['','## Recuperación','',f"`{recovery.read_text().strip()}`"]
 lines+=['','## Límites e interpretación',
  '', 'Los juicios son independientes del LLM y están incompletos. El score no es una probabilidad calibrada ni una verificación de verdad científica. El corpus es una muestra de 10.000 documentos, no el benchmark completo. TREC-COVID ya fue observado en trabajos anteriores: no se afirma una prueba ciega.',
  '', 'Los dos métodos comparten búsquedas y candidatos; el estudio atribuye diferencias a la puntuación final bajo esta configuración. No se agregan aquí los experimentos complementarios de los compañeros, que deberán identificarse por separado.',
  '', 'La conclusión de valor debe combinar la diferencia de relevancia y su incertidumbre con el coste de latencia. Una mejora de calidad no se presupone; no se cambia el prompt ni se descartan consultas para obtenerla.']
 (OUT/'informe.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 dump('verificacion_analisis.json',dict(quality_complete=complete,metric_rows=len(quality),
  performance_complete=(OUT/'rendimiento_completo.json').exists(),paired_bootstrap_rows=len(ci),
  latency_observations=len(latency),analysis_job=os.environ.get('SLURM_JOB_ID')))

def notebook():
 import nbformat
 from nbclient import NotebookClient
 kernel=ROOT/'jupyter/kernels/experiment';kernel.mkdir(parents=True,exist_ok=True)
 (kernel/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Scientific experiment',language='python')),encoding='utf-8')
 os.environ['JUPYTER_PATH']=str(ROOT/'jupyter')
 mdcell=nbformat.v4.new_markdown_cell;code=nbformat.v4.new_code_cell
 cells=[mdcell('# Búsqueda híbrida: fusión convexa frente a LLM\n\nAnálisis ejecutado de los resultados guardados en Slurm. No repite inferencias. Incluye el estado real y los fallos; no sustituye archivos ausentes por métricas inventadas.'),
  code("from pathlib import Path\nimport json\nimport pandas as pd\nfrom IPython.display import display, Image, Markdown\np=Path.cwd()/'resultados'\ndisplay(json.loads((p/'verificacion_analisis.json').read_text()))"),
  mdcell('## Calidad y diferencias pareadas'),
  code("for name in ['calidad_resumen.csv','diferencias_pareadas.csv','cobertura_qrels.csv','diagnostico_scores.json']:\n    f=p/name\n    if f.exists():\n        print(name)\n        display(pd.read_csv(f) if f.suffix=='.csv' else json.loads(f.read_text()))"),
  mdcell('## Batch, concurrencia y latencia'),
  code("for name in ['batches_resumen.csv','estabilidad_batches.csv','concurrencia_resumen.csv','latencia_resumen.csv']:\n    f=p/name\n    if f.exists():\n        print(name)\n        display(pd.read_csv(f))"),
  mdcell('## Figuras'),code("for f in sorted(p.glob('fig*.png')):\n    display(Image(filename=str(f)))"),
  mdcell('## Interpretación y limitaciones'),code("display(Markdown((p/'informe.md').read_text()))")]
 nb=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'experiment','display_name':'Scientific experiment','language':'python'}})
 path=ROOT/'experimentos_ejecutados.ipynb'
 try:NotebookClient(nb,kernel_name='experiment',timeout=300,allow_errors=False,resources={'metadata':{'path':str(ROOT)}}).execute()
 finally:nbformat.write(nb,path)
 code_cells=[c for c in nb.cells if c.cell_type=='code']
 assert all(c.execution_count is not None for c in code_cells)
 assert not [o for c in code_cells for o in c.outputs if o.output_type=='error']
 dump('notebook_verificado.json',dict(code_cells=len(code_cells),errors=0))

def accounting():
 idsfile=ROOT/'jobs.json'
 if idsfile.exists():
  jobs=json.loads(idsfile.read_text());ids=','.join(str(v) for k,v in jobs.items() if k.endswith('_job'))
  if ids:
   result=subprocess.run(['sacct','-j',ids,'--parsable2','--format=JobID,JobName,State,Elapsed,Start,End,NodeList,ExitCode'],capture_output=True,text=True)
   (OUT/'slurm_accounting.csv').write_text(result.stdout,encoding='utf-8')

if __name__=='__main__':
 analyze();notebook();accounting()
 hashes={str(p.relative_to(ROOT)):base.sha(p) for folder in ['resultados','entrada_comun'] for p in (ROOT/folder).rglob('*') if p.is_file()}
 dump('sha256_archivos.json',hashes)
 print('ANALYSIS_AND_NOTEBOOK_COMPLETE',flush=True)
