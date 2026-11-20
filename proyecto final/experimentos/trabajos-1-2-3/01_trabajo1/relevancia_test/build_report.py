"""Generate figures and execute the explained notebook inside a Slurm allocation."""
from pathlib import Path
import os,sys,json,time,hashlib,shutil
import pandas as pd
import nbformat
from minion_test import initialize, dump, sha
from minion_figures import figures

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'test_results'
compute_summary=json.loads((OUT/'run_summary.json').read_text())
assert compute_summary['stage']=='COMPUTE_COMPLETE'
ctx=dict(root=ROOT,out=OUT,pilot=False,alpha=json.loads((OUT/'alpha_usado.json').read_text()),
         started=time.monotonic(),summary=compute_summary)
notes=figures(ctx)
metrics=pd.read_csv(OUT/'metrics.csv'); boot=pd.read_csv(OUT/'bootstrap.csv')
cells=[]
def md(text): cells.append(nbformat.v4.new_markdown_cell(text))
def code(text): cells.append(nbformat.v4.new_code_cell(text))

md('# MINION — relevancia offline: fusión y reranking\n\n'
   'Evaluación final de **FiQA-test** y **TREC-COVID-test**, ejecutada en Khipu mediante Slurm. '
   '**α = 0,85** fue fijado en FiQA-dev y no se vuelve a ajustar. '
   'El corpus y los juicios se conservan tal como fueron publicados; no se entrenan modelos ni se seleccionan configuraciones con test.')
lines=[]
for _,b in boot.iterrows():
    m=metrics[metrics.dataset==b.dataset].set_index('route')
    lines.append(f"- **{b.dataset}:** P@3 fused {m.loc['fused','precision_at_3']:.4f}; reranked {m.loc['reranked','precision_at_3']:.4f}; Δ {b.delta_precision_at_3:+.4f}, IC 95 % [{b.ci_95_low:+.4f}, {b.ci_95_high:+.4f}].")
md('## 0. Resumen ejecutivo\n\n'+'\n'.join(lines)+
   '\n- La diferencia compara los mismos candidatos por consulta; solo cambia su orden.\n'
   '- Los IC usan 10.000 remuestreos pareados de consultas, semilla 42.\n'
   '- La cobertura de juicios y el resultado condensado se reportan como análisis de sensibilidad.')
md('## 1. Objetivo, protocolo y reproducibilidad\n\n'
   'Se pregunta si un cross-encoder mejora la relevancia del top 3 de la fusión híbrida. '
   'Una unidad de evaluación es una consulta; las métricas son promedios macro por consulta. '
   'El módulo `minion_test.py` acompaña este notebook y contiene los cálculos usados por los jobs. '
   'Las etapas costosas tienen caché: al reejecutar se verifican y reutilizan los puntajes ya calculados.')
code("import os, sys, json, time, gc\nfrom pathlib import Path\nimport pandas as pd\nfrom IPython.display import display, Image, Markdown\nROOT = Path(os.environ.get('MINION_ROOT', str(Path.cwd().parent))).resolve()\nOUT = ROOT / 'test_results'\nsys.path.insert(0, str(ROOT))\nfrom minion_test import load_dataset, retrieve, rerank, evaluate, sha\nalpha = json.loads((OUT / 'alpha_usado.json').read_text())\nassert alpha['alpha'] == 0.85 and not alpha['pilot']\nassert sha(OUT / 'alpha_usado.json') == sha(ROOT / 'results/alpha.json')\nctx = dict(root=ROOT, out=OUT, pilot=False, alpha=alpha, started=time.monotonic(),\n    summary=json.loads((OUT / 'run_summary.json').read_text()))\nprint('Python:', sys.executable)\nprint('α:', alpha['alpha'], '| revisión BGE:', alpha['model_revision'])\nprint('Job de cómputo:', ctx['summary']['job_id'], '| nodo:', ctx['summary']['node'])")
md('### Configuración congelada y desempates\n\n'
   'BM25 usa bm25s/lucene, k1=0,9, b=0,4, stopwords inglesas y PyStemmer english. '
   'BGE usa el prefijo especificado solo en consultas, CLS, forward fp16, normalización L2 en float32 y longitud máxima 512. '
   'Se busca con `faiss.IndexFlatIP`; los empates se resuelven por ID ascendente, incluso en el corte del top 10. '
   'El cross-encoder usa float32 y procesa todos los candidatos de una consulta en un lote. '
   'Sus empates conservan el orden fusionado. Los runs TREC usan puntajes monotónicos derivados del rango para conservar ese orden; los puntajes originales se guardan en parquet.')
code("display(pd.DataFrame([alpha['bm25']]))\ndisplay(pd.DataFrame([alpha['semantic']]))\nprint('Normalización:', alpha['normalization'])\nprint('Desempate:', alpha['document_tie_break'])\nprint('Reranker:', ctx['summary']['reranker'])")
md('## 2. Datos, auditoría y separación desarrollo/prueba\n\n'
   'FiQA contiene preguntas y pasajes financieros; TREC-COVID contiene consultas y artículos científicos sobre COVID-19. '
   'Se comprueban los conteos de ambos corpus y sus consultas de prueba; los qrels se usan solo para evaluar. '
   'No se eliminan textos vacíos ni duplicados: el corpus publicado queda intacto. '
   'TREC-COVID incluye dos entradas −1; `trec_eval` las interpreta como sin juicio. '
   'La métrica nDCG conserva los grados originales 0, 1 y 2 y el evaluador da ganancia cero a −1. '
   '[Convención oficial NIST](https://github.com/usnistgov/trec_eval/blob/main/formats.c).')
code("counts = json.loads((OUT / 'counts.json').read_text())\ndisplay(pd.DataFrame(counts).T)\nassert counts['fiqa']['corpus'] == 57638 and counts['fiqa']['test_queries'] == 648\nassert counts['trec-covid']['corpus'] == 171332 and counts['trec-covid']['test_queries'] == 50")
for ds,title in [('fiqa','FiQA-test'),('trec-covid','TREC-COVID-test')]:
    md(f'## 3. {title}: recuperación y fusión\n\n'
       'Se lee el corpus completo con texto `title + " " + text`. Solo se usan consultas del split test. '
       'La siguiente celda comprueba los datos y muestra un ejemplo real.')
    code(f"state = load_dataset(ctx, '{ds}')\nq = state['qids'][0]\nprint('Consulta:', q, state['queries'][q])\nprint('Documento de ejemplo:', state['docs'][0]['_id'], state['texts'][0][:500])")
    md('### Índice BM25, embeddings y candidatos\n\n'
       'Se reutilizan índices y embeddings compatibles. Para cada consulta se unen top 10 BM25 y top 10 denso por ID. '
       'Se calculan ambos puntajes de todos los candidatos, incluso cuando un documento llegó por una sola ruta. '
       'La normalización min-max se aplica dentro de esta unión; si el vector es constante se asigna 1. '
       'La fusión es `(1 − 0,85) × lex_norm + 0,85 × sem_norm`.')
    code("candidates = retrieve(ctx, state)\nassert candidates.groupby('query_id').size().between(10,20).all()\nprint('Candidatos:', len(candidates), '| consultas:', candidates.query_id.nunique())\ndisplay(candidates.head())")
    md('### Cross-encoder sobre exactamente los mismos documentos\n\n'
       'MiniLM puntúa los pares consulta-documento; no agrega ni elimina candidatos. '
       'Se guarda su puntaje original junto con los puntajes de recuperación. '
       'El caché permite ejecutar el notebook sin repetir inferencias ya terminadas.')
    code("runs = rerank(ctx, state)\nassert all(set(runs['fused'][q]) == set(runs['reranked'][q]) for q in state['qids'])\nprint('Igualdad de candidatos verificada en todas las consultas.')")
    md('### Métricas, contraste independiente y bootstrap pareado\n\n'
       'Se calculan P(rel≥1)@3, nDCG@3 y RR(rel≥1)@10 con `ir_measures`. '
       'Recall@20 se reporta solo para fused y promedia consultas con al menos un relevante. '
       'Un segundo cálculo explícito por consulta debe coincidir con el evaluador. '
       'Cada remuestreo usa los mismos IDs de consultas para fused y reranked; se reinicia `default_rng(42)` por dataset.')
    code(f"comparison = evaluate(ctx, state)\ndisplay(pd.read_csv(OUT / 'metrics.csv').query(\"dataset == '{ds}'\"))\ndisplay(pd.DataFrame([comparison]))\ndel state, candidates, runs\ngc.collect()")
md('## 4. Resultados visuales\n\n'
   'Todas las figuras fueron generadas con matplotlib y guardadas como PNG a 200 dpi. '
   'Los colores siguen Okabe–Ito. Los intervalos R1 son marginales; R2 presenta la diferencia pareada.')
order=['R3_alpha_fiqa_dev.png']
for ds in ['fiqa','trec-covid']:
    order += [f'R{k}_{name}_{ds}.png' for k,name in [(1,'metricas'),(2,'bootstrap'),(4,'matriz_transicion'),
              (5,'gana_empata_pierde'),(6,'matriz_posiciones'),(7,'origen_candidatos'),(8,'judged')]]
for name in order:
    md('### '+name.replace('.png','').replace('_',' '))
    code(f"display(Image(filename=str(OUT / 'figs' / '{name}')))")
    md(notes[name])
md('## 5. Juicios faltantes y ejemplos\n\n'
   'Judged@10 sigue literalmente la presencia del par consulta-documento en los qrels, incluido grado 0. '
   'La lista condensada elimina documentos cuyo par no aparece en qrels antes de calcular las métricas. '
   'Las dos entradas −1 se conservan y se audita si fueron recuperadas; no se alteran las etiquetas. '
   'La condensación de estas listas cortas es un análisis de sensibilidad, no una estimación de relevancia completa. '
   'FiQA solo tiene qrels positivos: al condensar se eliminan todos los negativos no juzgados y P@3 queda determinada por '
   'el número de relevantes en los mismos candidatos, por lo que la diferencia se fuerza a cero. Esto no demuestra ausencia de sesgo.')
code("display(pd.read_csv(OUT / 'judged.csv'))\ndisplay(pd.read_csv(OUT / 'condensed.csv'))\ndisplay(Markdown((OUT / 'R9_ejemplos.md').read_text()))")
md('## 6. Tabla para el paper y rutas de respaldo\n\n'
   'Si falla el reranker, la ruta de respaldo es fused; si falla la ruta semántica, lex; si falla la ruta léxica, sem. '
   'La tabla incluye relevancia, incertidumbre y cobertura de juicios. Estos resultados no miden latencia ni verifican un SLO.')
code("display(pd.read_csv(OUT / 'paper_table.csv').T)\nprint('Run files:', sorted(p.name for p in (OUT / 'runs').glob('*.trec')))")
conclusion=[]
for _,b in boot.iterrows():
    direction='mejora' if b.delta_precision_at_3>0 else ('empeora' if b.delta_precision_at_3<0 else 'empata')
    excludes='excluye cero' if b.ci_95_low>0 or b.ci_95_high<0 else 'incluye cero'
    conclusion.append(f'- En **{b.dataset}**, el cross-encoder {direction} P@3 en promedio: Δ = {b.delta_precision_at_3:+.4f} ({100*b.delta_precision_at_3:+.2f} puntos porcentuales).')
    conclusion.append(f'- Su IC pareado 95 % [{b.ci_95_low:+.4f}, {b.ci_95_high:+.4f}] {excludes}; la Δ condensada es {b.condensed_delta_precision_at_3:+.4f} y el signo {"se mantiene" if b.delta_sign_preserved else "cambia"}.')
    if b.dataset=='fiqa': conclusion[-1]+=' El empate condensado es estructural porque FiQA solo contiene juicios positivos.'
conclusion += ['- Se aplicó el mismo α=0,85 a ambos tests, sin selección de hiperparámetros sobre prueba.',
 '- El reranker únicamente reordena: no puede rescatar relevantes ausentes de la unión de candidatos.',
 '- Los juicios incompletos, los textos truncados a 512 tokens y la transferencia del modelo a dominios distintos limitan la interpretación.',
 '- El resultado es una evaluación de relevancia offline; no demuestra una mejora bajo un presupuesto de latencia.']
md('## 7. Conclusión y limitaciones\n\n'+'\n'.join(conclusion))
md('## 8. Procedencia y archivos\n\n'
   'Se adjuntan el script de evaluación, el generador de figuras, los runs TREC, los puntajes parquet, los datos por consulta, '
   'las muestras bootstrap y la contabilidad Slurm. El α validado se copia byte por byte; la curva de desarrollo solo se visualiza.')
code("print('α SHA-256:', sha(OUT / 'alpha_usado.json'))\nprint('Candidatos SHA-256:')\nfor ds in ['fiqa','trec-covid']:\n    print(ds, sha(OUT / f'cands_{ds}_test.parquet'))\nassert len(list((OUT / 'figs').glob('*.png'))) == 15\nassert len(pd.read_csv(OUT / 'bootstrap.csv')) == 2\nprint('Verificación del notebook completada.')")
nb=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'minion-test','display_name':'Python (Khipu MINION)','language':'python'}})
percent=[]
for cell in cells:
    if cell.cell_type=='markdown':
        percent.append('# %% [markdown]\n'+'\n'.join('# '+line for line in cell.source.splitlines()))
    else:
        percent.append('# %%\n'+cell.source)
(OUT/'trabajo1_relevancia.py').write_text('\n\n'.join(percent)+'\n')
spec=ROOT/'runtime/kernels/minion-test'; spec.mkdir(parents=True,exist_ok=True)
dump(spec/'kernel.json',dict(argv=[str(ROOT/'.venv/bin/python'),'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Python (Khipu MINION)',language='python'))
os.environ['JUPYTER_PATH']=str(ROOT/'runtime')
from nbclient import NotebookClient
path=OUT/'trabajo1_relevancia.ipynb'
try:
    NotebookClient(nb,timeout=1800,kernel_name='minion-test',allow_errors=False,
        resources={'metadata':{'path':str(OUT)}}).execute()
finally:
    nbformat.write(nb,path)
errors=[o for c in nb.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='error']
assert not errors and all(c.execution_count is not None for c in nb.cells if c.cell_type=='code')
compute_summary['stage']='COMPLETE_VERIFIED'
compute_summary['notebook_code_cells']=sum(c.cell_type=='code' for c in nb.cells)
compute_summary['notebook_errors']=len(errors)
compute_summary['figures']=15
compute_summary['script_sha256']=sha(ROOT/'minion_test.py')
compute_summary['notebook_sha256']=sha(path)
dump(OUT/'run_summary.json',compute_summary)
for name in ['minion_test.py','minion_figures.py','build_report.py','test_eval.sbatch','prepare_test.py','prepared_test.json']:
    shutil.copy2(ROOT/name,OUT/name)
dump(OUT/'manifest.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json'})
print('NOTEBOOK_COMPLETE_VERIFIED',len(nb.cells),'cells',flush=True)
