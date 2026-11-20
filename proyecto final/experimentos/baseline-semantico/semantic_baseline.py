"""Independent semantic-only baseline, matched convex control and paired quality CIs."""
from pathlib import Path
import argparse,csv,hashlib,json,math,os,random,socket,time,concurrent.futures as cf
import numpy as np

ROOT=Path(__file__).resolve().parent
OLD=Path('/home/usuario/projects/minion_experimentos_cientificos_20261119')
BGE=Path('/home/usuario/projects/minion_trec_khipu_v4_20261118/hf_home/hub/models--BAAI--bge-base-en-v1.5/snapshots/a5beb1e3e68b9ab74eb54cfd186867f64f240e1a')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def csvwrite(p,rows):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def rank(ids,s):return sorted(range(len(ids)),key=lambda i:(-float(s[i]),ids[i]))
def norm(a):return np.ones_like(a) if a.max()==a.min() else (a-a.min())/(a.max()-a.min())
def metrics(ids,rel):
 r=[max(0,rel.get(d,0)) for d in ids]
 dcg=lambda a:sum((2**g-1)/math.log2(i+2) for i,g in enumerate(a[:3]))
 ideal=dcg(sorted(rel.values(),reverse=True))
 return dict(P3=sum(v>0 for v in r[:3])/3,nDCG3=dcg(r)/ideal if ideal else 0.,MRR10=next((1/(i+1) for i,v in enumerate(r[:10]) if v>0),0.))
def selftest():
 assert rank(['b','a'],[1,1])==[1,0]
 assert metrics(['x','y'],{'y':1})['MRR10']==.5
 assert np.allclose(norm(np.array([2.,2.])),1)

def main(args):
 import torch,faiss,bm25s,Stemmer
 from transformers import AutoTokenizer,AutoModel
 from torch._native.registry import deregister_op_overrides
 deregister_op_overrides(disable_dispatch_keys='CUDA');torch.set_num_threads(1 if args.dataset=='trec' else 4)
 torch.backends.cuda.matmul.allow_tf32=False
 assert torch.cuda.is_available();selftest()
 out=ROOT/args.dataset/('smoke' if args.smoke else 'resultados');out.mkdir(parents=True,exist_ok=True)
 assert not (out/'completado.json').exists(),'Use a fresh output folder'
 folder=OLD/'entrada_comun' if args.dataset=='trec' else ROOT/'fiqa'
 corpus=folder/'corpus_10000.jsonl' if args.dataset=='trec' else folder/'corpus.jsonl'
 if args.dataset=='fiqa':assert sha(corpus)=='ccf561f4f3ef6c2d9f06e80bcc8194192abfcdac9726e2390775e6c43b833bd8'
 docs=[json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines()]
 ids=[str(r['_id']) for r in docs];lookup=set(ids);assert len(ids)==len(lookup)==10000
 texts=[(r.get('title','')+' '+r['text']).strip() for r in docs]
 queries={str(r['_id']):r['text'] for r in map(json.loads,(folder/'consultas.jsonl' if args.dataset=='trec' else folder/'queries.jsonl').read_text(encoding='utf-8').splitlines())}
 rel={}
 qrel=folder/'qrels.tsv' if args.dataset=='trec' else folder/'test.tsv'
 with qrel.open(encoding='utf-8') as f:
  for r in csv.DictReader(f,delimiter='\t'):
   q,d,g=r['query-id'],r['corpus-id'],int(r['score'])
   rel.setdefault(q,{})
   if d in lookup and g>=0:rel[q][d]=g
 qids=sorted(q for q in rel if q in queries)
 assert len(qids)==(50 if args.dataset=='trec' else 648)
 if args.smoke:qids=qids[:2]
 tok=AutoTokenizer.from_pretrained(str(BGE));model=AutoModel.from_pretrained(str(BGE)).cuda().half().eval()
 def encode(texts):
  x=tok(texts,padding=True,truncation=True,max_length=512,return_tensors='pt').to('cuda')
  with torch.inference_mode():v=torch.nn.functional.normalize(model(**x).last_hidden_state[:,0].float(),p=2,dim=1)
  result=v.cpu().numpy().astype('float32');assert np.isfinite(result).all();return result
 cache=OLD/'resultados/semantic.faiss' if args.dataset=='trec' else ROOT/'fiqa/semantic.faiss'
 if cache.exists():index=faiss.read_index(str(cache))
 else:
  vectors=np.concatenate([encode(texts[i:i+32]) for i in range(0,len(texts),32)])
  index=faiss.IndexFlatIP(vectors.shape[1]);index.add(vectors);faiss.write_index(index,str(cache))
 assert index.ntotal==10000;faiss.omp_set_num_threads(1)
 stem=Stemmer.Stemmer('english');tokens=bm25s.tokenize(texts,stopwords='en',stemmer=stem,show_progress=False)
 bm=bm25s.BM25(method='lucene',k1=.9,b=.4);bm.index(tokens,show_progress=False)
 def semantic(q):
  v=encode(['Represent this sentence for searching relevant passages: '+q]);ds,ii=index.search(v,len(ids))
  scores=np.empty(len(ids));scores[ii[0]]=ds[0];return scores
 def lexical(q):
  ts=bm25s.tokenize(q,stopwords='en',stemmer=stem,return_ids=False,show_progress=False)[0]
  return np.asarray(bm.get_scores(ts),float) if ts else np.zeros(len(ids))
 def search(q,method):
  if method=='semantic':
   s=semantic(q);order=rank(ids,s)[:10];return [ids[i] for i in order],[float(s[i]) for i in order]
  with cf.ThreadPoolExecutor(max_workers=2) as pool:
   f=pool.submit(lexical,q);s=semantic(q);l=f.result()
  c=sorted(set(rank(ids,s)[:10])|set(rank(ids,l)[:10]),key=lambda i:ids[i])
  score=.15*norm(l[c])+.85*norm(s[c]);order=rank([ids[i] for i in c],score)
  return [ids[c[i]] for i in order],[float(score[i]) for i in order]
 reference={}
 if args.dataset=='trec':
  with (OLD/'resultados/calidad_por_consulta.csv').open() as f:
   for r in csv.DictReader(f):
    if r['method'] in ['fusion','LLM']:reference[r['qid'],r['method']]={k:float(r[k]) for k in ['P3','nDCG3','MRR10']}
 else:
  with (ROOT/'fiqa/metrics_per_query.csv').open() as f:
   for r in csv.DictReader(f):reference[r['query_id'],'fusion' if r['arm']=='A' else 'LLM']={k:float(r[v]) for k,v in [('P3','p@3'),('nDCG3','ndcg@3'),('MRR10','mrr@10')]}
 search(queries[qids[0]],'semantic');search(queries[qids[0]],'fusion_matched')
 rows=[];ranks={};drift=[]
 for q in qids:
  ranks[q]={}
  for method in ['semantic','fusion_matched']:
   ranking,scores=search(queries[q],method);m=metrics(ranking,rel[q]);rows.append(dict(qid=q,method=method,**m));ranks[q][method]=ranking
   if method=='semantic':
    pass
   else:drift.append(dict(qid=q,**{k:m[k]-reference[q,'fusion'][k] for k in m}))
  for method in ['fusion','LLM']:rows.append(dict(qid=q,method=method+'_reference',**reference[q,method]))
 csvwrite(out/'metricas_por_consulta.csv',rows);dump(out/'rankings.json',ranks);csvwrite(out/'diferencias_control_vs_fusion_previa.csv',drift)
 summary=[dict(method=m,**{k:float(np.mean([r[k] for r in rows if r['method']==m])) for k in ['P3','nDCG3','MRR10']}) for m in ['semantic','fusion_matched','fusion_reference','LLM_reference']]
 csvwrite(out/'metricas_resumen.csv',summary)
 by={(r['qid'],r['method']):r for r in rows};ci=[];rng=np.random.default_rng(42)
 for method in ['fusion_matched','fusion_reference','LLM_reference']:
  for metric in ['P3','nDCG3','MRR10']:
   delta=np.array([by[q,method][metric]-by[q,'semantic'][metric] for q in qids]);boot=delta[rng.integers(0,len(delta),size=(10000,len(delta)))].mean(1)
   low,high=np.quantile(boot,[.025,.975]);ci.append(dict(comparison=method+' minus semantic',metric=metric,delta=float(delta.mean()),ci95_low=float(low),ci95_high=float(high),queries=len(qids),seed=42,resamples=10000))
 csvwrite(out/'diferencias_pareadas.csv',ci)
 timing=[]
 for i in range(3 if args.smoke else 1000):
  methods=['semantic','fusion_matched'];random.Random(42+i).shuffle(methods)
  for method in methods:
   q=qids[i%len(qids)];torch.cuda.synchronize();t=time.perf_counter();ranking,_=search(queries[q],method);torch.cuda.synchronize()
   assert ranking==ranks[q][method]
   timing.append(dict(request=i,qid=q,method=method,seconds=time.perf_counter()-t,status='ok'))
 csvwrite(out/'latencia_solicitudes.csv',timing)
 tails=[]
 for method in ['semantic','fusion_matched']:
  v=np.array([r['seconds'] for r in timing if r['method']==method]);tails.append(dict(method=method,requests=len(v),mean_seconds=float(v.mean()),p50_seconds=float(np.quantile(v,.5)),p95_seconds=float(np.quantile(v,.95)),p99_seconds=float(np.quantile(v,.99)),errors=0))
 csvwrite(out/'latencia_resumen.csv',tails)
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(8,4));x=np.arange(3)
 for j,row in enumerate(summary):ax.bar(x+(j-1.5)*.2,[row[k] for k in ['P3','nDCG3','MRR10']],.2,label=row['method'])
 ax.set_xticks(x,['P@3','nDCG@3','MRR@10']);ax.set_ylim(0,1);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(out/'comparacion_calidad.png',dpi=160);plt.close(fig)
 dump(out/'protocolo.json',dict(dataset=args.dataset,smoke=args.smoke,documents=10000,queries=len(qids),
  corpus_sha256=sha(corpus),qrels_sha256=sha(qrel),index_sha256=sha(cache),code_sha256=sha(__file__),
  model='BAAI/bge-base-en-v1.5',revision=BGE.name,pooling='CLS L2',precision='fp16 forward, normalized float32',query_max_length=512,
  semantic_baseline='Full selected corpus search; no lexical search, candidate union, convex fusion or LLM in semantic requests',
  matched_control='BM25 and semantic search in parallel, same union and alpha_semantic0.85; rerun in same job',
  references='Saved main experiment quality scores, no new LLM inference; latency references not pooled',
  node=socket.gethostname(),gpu=torch.cuda.get_device_name(),torch=torch.__version__,job=os.environ.get('SLURM_JOB_ID'),
  positive_coverage=sum(any(v>0 for v in rel[q].values()) for q in qids),warmup_excluded=True,latency_requests_each=3 if args.smoke else 1000,
  reference_fusion_max_metric_drift={k:max(abs(r[k]) for r in drift) for k in ['P3','nDCG3','MRR10']},
  limitations=['Prior exposed datasets','FiQA environment differs from prior run; matched fusion control remeasured','Shared GPU contention not controlled']))
 report=['# Solo semántica: '+args.dataset,'','Prueba corta' if args.smoke else 'Corrida completa','',json.dumps(summary,ensure_ascii=False,indent=2),
  '\nComparaciones pareadas: diferencias_pareadas.csv. Los IC que incluyen cero no prueban igualdad.',
  '\nLa latencia compara solo semántica y fusión recalculada en el mismo job. El LLM se conserva como referencia de calidad, sin repetir su inferencia.',
  '\nLas diferencias del control frente a la fusión anterior se conservan; no se ocultan ni se atribuyen solo a un factor.']
 (out/'informe.md').write_text('\n'.join(report),encoding='utf-8')
 import nbformat,sys
 from nbclient import NotebookClient
 kernel=ROOT/'jupyter/kernels/semantic';kernel.mkdir(parents=True,exist_ok=True)
 dump(kernel/'kernel.json',dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Semantic baseline',language='python'))
 os.environ['JUPYTER_PATH']=str(ROOT/'jupyter')
 cells=[nbformat.v4.new_markdown_cell('# Baseline semántico: '+args.dataset+'\n\nResultados reales guardados por Slurm. Las referencias de calidad provienen de corridas anteriores; la fusión de control se midió junto a este baseline.'),
  nbformat.v4.new_code_cell("from pathlib import Path\nimport pandas as pd\nfrom IPython.display import display, Image\np=Path.cwd()\ndisplay(pd.read_csv(p/'metricas_resumen.csv'))\ndisplay(pd.read_csv(p/'diferencias_pareadas.csv'))"),
  nbformat.v4.new_code_cell("display(pd.read_csv(p/'latencia_resumen.csv'))\ndisplay(Image(filename=str(p/'comparacion_calidad.png')))"),
  nbformat.v4.new_code_cell("import json\ndisplay(json.loads((p/'protocolo.json').read_text()))")]
 nb=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'semantic','display_name':'Semantic baseline','language':'python'}})
 try:NotebookClient(nb,kernel_name='semantic',timeout=180,allow_errors=False,resources={'metadata':{'path':str(out)}}).execute()
 finally:nbformat.write(nb,out/'baseline_semantico_ejecutado.ipynb')
 dump(out/'completado.json',dict(ok=True,smoke=args.smoke,queries=len(qids),latency_requests=len(timing),job=os.environ.get('SLURM_JOB_ID')))
 print('SEMANTIC_BASELINE_COMPLETE',args.dataset,args.smoke,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dataset',choices=['trec','fiqa']);p.add_argument('--smoke',action='store_true');p.add_argument('--self-test',action='store_true');args=p.parse_args()
 if args.self_test:selftest();print('SELF_TEST_OK')
 else:main(args)
