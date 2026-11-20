"""Frozen main experiment. Execute quality then performance through Slurm only."""
from pathlib import Path
import argparse, concurrent.futures as cf, csv, gc, hashlib, importlib.metadata as md
import json, math, os, random, socket, sqlite3, subprocess, sys, threading, time, traceback
import numpy as np
import base

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'resultados'
COMMON=ROOT/'entrada_comun'
base.OUT=OUT
START=time.monotonic()

def dump(name,obj):base.dump(OUT/name,obj)
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def csvout(name,rows):base.csvout(name,rows)
def log(s):base.log(s)
def sync():
 import torch
 torch.cuda.synchronize()
def finite(rows):
 assert rows and all(np.isfinite(r['score']) and 0<=r['score']<=1 for r in rows)
def timed_score(scorer,pairs,batch):
 sync();t=time.perf_counter();rows,eff=scorer.score(pairs,batch);sync()
 finite(rows)
 return rows,eff,time.perf_counter()-t

def environment(stage):
 import torch
 from torch._native.registry import deregister_op_overrides
 deregister_op_overrides(disable_dispatch_keys='CUDA')
 assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
 torch.set_num_threads(1);torch.manual_seed(42);np.random.seed(42)
 torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
 assert (ROOT/'preflight_ok.json').exists(),'Real-model preflight must pass first'
 OUT.mkdir(exist_ok=True);COMMON.mkdir(exist_ok=True)
 dump(f'entorno_{stage}.json',dict(stage=stage,job=os.environ.get('SLURM_JOB_ID'),node=socket.gethostname(),
   gpu=torch.cuda.get_device_name(),gpu_memory_bytes=torch.cuda.get_device_properties(0).total_memory,
   precision_llm='float32',backend='standard ATen; native CUDA overrides disabled',
   python=sys.version,libraries={k:md.version(k) for k in ['torch','transformers','numpy','bm25s','faiss-cpu']},
   nvidia_smi=subprocess.check_output(['nvidia-smi'],text=True),started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))

def prepare():
 rows=[json.loads(x) for x in (base.SOURCE/'corpus.jsonl').open(encoding='utf-8')]
 docs=sorted(random.Random(42).sample(rows,10000),key=lambda r:str(r['_id']));del rows
 ids={str(r['_id']) for r in docs}
 with (COMMON/'corpus_10000.jsonl').open('w',encoding='utf-8') as f:
  for row in docs:f.write(json.dumps(row,ensure_ascii=False)+'\n')
 (COMMON/'corpus_ids.txt').write_text('\n'.join(str(r['_id']) for r in docs)+'\n',encoding='utf-8')
 queries={str(q['_id']):q['text'] for q in map(json.loads,(base.SOURCE/'queries.jsonl').open(encoding='utf-8'))}
 rel={q:{} for q in queries};qrows=[]
 with (base.SOURCE/'qrels/test.tsv').open() as f:
  for r in csv.DictReader(f,delimiter='\t'):
   q,d,g=r['query-id'],r['corpus-id'],int(r['score'])
   if d in ids and g>=0:rel[q][d]=g;qrows.append((q,d,g))
 with (COMMON/'qrels.tsv').open('w',encoding='utf-8') as f:
  f.write('query-id\tcorpus-id\tscore\n')
  for q,d,g in qrows:f.write(f'{q}\t{d}\t{g}\n')
 with (COMMON/'consultas.jsonl').open('w',encoding='utf-8') as f:
  for q in sorted(queries,key=int):f.write(json.dumps(dict(_id=q,text=queries[q]),ensure_ascii=False)+'\n')
 qids=sorted(queries,key=int);random.Random(43).shuffle(qids)
 if os.environ.get('EXPERIMENT_SMOKE')=='1':qids=qids[:2]
 (COMMON/'prompt_principal.txt').write_text(base.PROMPT,encoding='utf-8')
 if (ROOT/'entorno_pip.txt').exists():(COMMON/'requisitos_instalados.txt').write_text((ROOT/'entorno_pip.txt').read_text(),encoding='utf-8')
 dump('consultas.json',queries);dump('qrels.json',rel)
 csvout('cobertura_qrels.csv',[dict(qid=q,positive_in_subset=sum(g>0 for g in rel[q].values()),judged_in_subset=len(rel[q])) for q in qids])
 protocol=dict(dataset='TREC-COVID',documents=10000,queries=len(qids),smoke=os.environ.get('EXPERIMENT_SMOKE')=='1',sampling='uniform without replacement; no positive injection',
  seeds=dict(corpus=42,query_order=43,bootstrap=42,batch_order=44,latency_order=45),query_order=qids,complementary_queries=qids[:10],
  candidate_union='top10 lexical union top10 semantic by ID; original document; max20',
  alpha_semantic=.85,alpha_origin='previous FiQA-dev, no tuning on TREC',normalization='per-query minmax on candidate union; constant columns map to ones',
  tie_break='ascending string document ID',LLM_model=json.loads((ROOT/'modelo_preparado.json').read_text()),
  LLM_precision='float32',LLM_max_tokens=1024,semantic_max_tokens=512,prompt=base.PROMPT,
  score='conditional expected digit0..4 /4; label mass separately recorded; no forced invalid-score replacement',
  primary_batch=4,batch_candidates=[1,4,8],batch_repeats=3,batch_stability=dict(max_absolute_score_difference=.001,identical_top3=True),
  concurrency=[1,2,4],concurrency_requests_each=50,latency_max_requests_per_method=1000,
  latency_scope='warm models, complete retrieval+union+scoring+sort; no answer or score cache',
  ndcg_gain='2**relevance-1',ndcg_ideal='all judged documents in selected corpus, not just candidates',
  unjudged='contributes zero in conventional metrics, distinguished in exports',
  negative_qrels='excluded from evaluable labels',metrics_queries='all50 plus positive-coverage subset',
  inference_validity='finite scores in [0,1], fail on NaN/Inf; no silent model or batch fallback',
  prior_exposure='TREC-COVID official test was used in earlier project work; exploratory, not blind validation',
  limitations=['10k subset','incomplete relevance judgments','50 queries only','closed-loop load','MIG hardware specific','no production availability claim'])
 protocol['hashes']={p.name:base.sha(p) for p in COMMON.iterdir() if p.is_file()}
 protocol['code_hashes']={p.name:base.sha(p) for p in ROOT.glob('*.py')}
 dump('protocolo.json',protocol);base.dump(COMMON/'manifiesto.json',protocol)
 return docs,queries,rel,qids

def checkpoint_worker(path,source,stop):
 rows=json.loads(Path(source).read_text(encoding='utf-8'))
 con=sqlite3.connect(path);con.execute('CREATE TABLE IF NOT EXISTS scores(q TEXT,d TEXT,s REAL,PRIMARY KEY(q,d))')
 for i,r in enumerate(rows):
  con.execute('INSERT OR IGNORE INTO scores VALUES (?,?,?)',(r['qid'],r['docid'],r['score']));con.commit()
  if stop and i+1==stop:os._exit(77)
 con.close()

def recovery(raw):
 sample=raw[:min(40,len(raw))];assert len(sample)>3
 source=OUT/'recuperacion_referencia.json';base.dump(source,sample)
 db=OUT/'recuperacion_prueba.sqlite'
 if db.exists():raise RuntimeError('Recovery test requires fresh database')
 command=[sys.executable,str(Path(__file__)), 'recovery-worker','--database',str(db),'--source',str(source)]
 first=subprocess.run(command+['--stop','3'],check=False)
 assert first.returncode==77
 partial=sqlite3.connect(db).execute('SELECT COUNT(*) FROM scores').fetchone()[0]
 subprocess.run(command,check=True);subprocess.run(command,check=True)
 con=sqlite3.connect(db);actual=con.execute('SELECT q,d,s FROM scores ORDER BY q,d').fetchall();con.close()
 expected=sorted([(r['qid'],r['docid'],r['score']) for r in sample])
 assert actual==expected and partial==3
 dump('recuperacion.json',dict(passed=True,interrupted_process_exit=77,committed_before_stop=partial,
  expected=len(expected),actual=len(actual),duplicate_rows=0,missing_rows=0,
  scope='real abrupt subprocess exit, committed score checkpoint and replay; stored reference scores, no model re-inference or machine failure'))

def quality():
 environment('quality');base.selftest()
 assert not (OUT/'calidad_completa.json').exists(),'Use a new folder for a new experiment'
 docs,queries,rel,qids=prepare()
 t=time.perf_counter();retriever=base.Retriever(docs);sync()
 dump('preparacion.json',dict(seconds=time.perf_counter()-t,excluded_from_warm_query_latency=True))
 candidates={};retrieval=[]
 retriever.search(queries[qids[0]])
 for q in qids:
  sync();t=time.perf_counter();c=retriever.search(queries[q]);sync()
  retrieval.append(dict(qid=q,seconds=time.perf_counter()-t,pairs=len(c)))
  assert len({r['id'] for r in c})==len(c)<=20
  candidates[q]=c
 dump('candidatos.json',candidates);base.dump(COMMON/'candidatos.json',candidates)
 csvout('recuperacion_busqueda.csv',retrieval)
 texts={str(d['_id']):(d.get('title','')+' '+d['text']).strip() for d in docs}
 dump('textos_candidatos.json',{r['id']:texts[r['id']] for c in candidates.values() for r in c})
 common_scores=[]
 for q,c in candidates.items():
  l=base.minmax([r['lex'] for r in c]);s=base.minmax([r['sem'] for r in c])
  lr=base.rank([r['id'] for r in c],[r['lex'] for r in c]);sr=base.rank([r['id'] for r in c],[r['sem'] for r in c])
  for i,r in enumerate(c):common_scores.append(dict(qid=q,docid=r['id'],lexical=r['lex'],semantic=r['sem'],
   lexical_normalized=float(l[i]),semantic_normalized=float(s[i]),fused=r['fused'],
   lexical_top10_position=lr.index(i)+1 if lr.index(i)<10 else '',semantic_top10_position=sr.index(i)+1 if sr.index(i)<10 else ''))
 # True original top-list positions exported below; no rank is inferred from the union for membership.
 for q in qids:
  l=retriever.lex(queries[q]);s=retriever.sem(queries[q])
  li={retriever.ids[i]:p+1 for p,i in enumerate(base.rank(retriever.ids,l)[:10])}
  si={retriever.ids[i]:p+1 for p,i in enumerate(base.rank(retriever.ids,s)[:10])}
  for r in common_scores:
   if r['qid']==q:r['lexical_top10_position']=li.get(r['docid'],'');r['semantic_top10_position']=si.get(r['docid'],'')
 with (COMMON/'scores_lexicos_semanticos.csv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(common_scores[0]));writer.writeheader();writer.writerows(common_scores)
 import torch
 del retriever.model;gc.collect();torch.cuda.empty_cache()
 scorer=base.Scorer();timed_score(scorer,[('What is ACE2?','ACE2 is a receptor protein.')],1)
 raw=[];rows=[];timing=[];rankings={}
 db=sqlite3.connect(OUT/'scores_checkpoint.sqlite')
 db.execute('CREATE TABLE IF NOT EXISTS scores(q TEXT,d TEXT,payload TEXT,PRIMARY KEY(q,d))')
 for q in qids:
  c=candidates[q];pairs=[(queries[q],texts[r['id']]) for r in c]
  sc,eff,seconds=timed_score(scorer,pairs,4)
  ids=[r['id'] for r in c]
  ranks={'fusion':base.rank(ids,[r['fused'] for r in c]),'LLM':base.rank(ids,[r['score'] for r in sc]),
    'BM25':base.rank(ids,[r['lex'] for r in c]),'semantic':base.rank(ids,[r['sem'] for r in c])}
  rankings[q]={m:[ids[i] for i in order] for m,order in ranks.items()}
  assert set(rankings[q]['fusion'])==set(rankings[q]['LLM'])==set(ids)
  for method,order in ranks.items():rows.append(dict(qid=q,method=method,**base.metrics([ids[i] for i in order],rel[q])))
  for r,s in zip(c,sc):
   row=dict(qid=q,docid=r['id'],relevance=rel[q].get(r['id']),**s);raw.append(row)
   db.execute('INSERT INTO scores VALUES (?,?,?)',(q,r['id'],json.dumps(row,allow_nan=False)))
  db.commit()
  timing.append(dict(qid=q,pairs=len(pairs),seconds=seconds,batch=4,effective_batch=eff))
  dump('scores_llm.json',raw);dump('rankings.json',rankings)
  csvout('calidad_por_consulta.csv',rows);csvout('tiempos_calidad.csv',timing)
  log(f'QUALITY {q}: {len(c)} pairs in {seconds:.3f}s')
 assert db.execute('SELECT COUNT(*) FROM scores').fetchone()[0]==len(raw)
 db.close();recovery(raw)
 manifest=json.loads((COMMON/'manifiesto.json').read_text())
 manifest['input_hashes_completed']={p.name:base.sha(p) for p in COMMON.iterdir() if p.is_file() and p.name!='manifiesto.json'}
 base.dump(COMMON/'manifiesto.json',manifest)
 dump('calidad_completa.json',dict(ok=True,queries=len(qids),pairs=len(raw),metric_rows=len(rows),seconds=time.monotonic()-START,job=os.environ.get('SLURM_JOB_ID')))
 log('QUALITY_COMPLETE')

class Searcher(base.Retriever):
 def __init__(self,docs):
  import torch,bm25s,Stemmer,faiss
  from transformers import AutoTokenizer,AutoModel
  self.torch=torch;self.bm25s=bm25s;self.stem=Stemmer.Stemmer('english')
  self.ids=[str(r['_id']) for r in docs];self.texts=[(r.get('title','')+' '+r['text']).strip() for r in docs]
  self.bm=bm25s.BM25.load(str(OUT/'bm25_index'),load_corpus=False)
  self.index=faiss.read_index(str(OUT/'semantic.faiss'));faiss.omp_set_num_threads(1)
  assert self.index.ntotal==len(self.ids)
  self.tok=AutoTokenizer.from_pretrained(str(base.BGE));self.model=AutoModel.from_pretrained(str(base.BGE)).cuda().half().eval()

class Engine:
 """One model instance, one serialized GPU execution lane, bounded clients.

 GPU mutex serializes query embedding and LLM forwards; CPU BM25 overlaps.
 Closed-loop clients count query concurrency, never model replicas.
 """
 def __init__(self,retriever,scorer,queries,expected,batch):
  self.r=retriever;self.s=scorer;self.q=queries;self.expected=expected;self.batch=batch;self.gpu=threading.Lock()
 def request(self,q,method,submitted):
  entered=time.perf_counter();wait=0.;gpu_queue=0.
  t=time.perf_counter()
  def semantic():
   nonlocal gpu_queue
   a=time.perf_counter()
   with self.gpu:
    gpu_queue+=time.perf_counter()-a
    return self.r.sem(self.q[q])
  with cf.ThreadPoolExecutor(max_workers=2) as pool:
   l=pool.submit(self.r.lex,self.q[q]);s=pool.submit(semantic);l,s=l.result(),s.result()
  retrieval_s=time.perf_counter()-t
  t=time.perf_counter()
  candidates=sorted(set(base.rank(self.r.ids,l)[:10])|set(base.rank(self.r.ids,s)[:10]),key=lambda i:self.r.ids[i])
  ids=[self.r.ids[i] for i in candidates]
  if set(ids)!={r['id'] for r in self.expected[q]}:raise AssertionError('Candidate union drift')
  union_s=time.perf_counter()-t;t=time.perf_counter();effective=0
  if method=='LLM':
   pairs=[(self.q[q],self.r.texts[i]) for i in candidates]
   a=time.perf_counter()
   with self.gpu:
    wait=time.perf_counter()-a
    scores,effective,_=timed_score(self.s,pairs,self.batch)
   order=base.rank(ids,[s['score'] for s in scores])
  else:
   fused=.15*base.minmax(l[candidates])+.85*base.minmax(s[candidates]);order=base.rank(ids,fused)
  scoring_s=time.perf_counter()-t
  elapsed=time.perf_counter()-submitted
  return dict(qid=q,method=method,status='ok',error='',seconds=elapsed,worker_start_delay_seconds=entered-submitted,
   retrieval_seconds=retrieval_s,union_seconds=union_s,final_ranking_seconds=scoring_s,
   llm_gpu_queue_seconds=wait,semantic_gpu_queue_seconds=gpu_queue,pairs=len(ids),effective_batch=effective,
   top3='|'.join(ids[i] for i in order[:3]))

def performance():
 environment('performance')
 assert read('calidad_completa.json')['ok']
 protocol=read('protocolo.json');queries=read('consultas.json');candidates=read('candidatos.json');texts=read('textos_candidatos.json')
 qids=protocol['query_order'];selected=qids[:10]
 scorer=base.Scorer();timed_score(scorer,[('What is ACE2?','ACE2 is a protein.')],1)
 import torch
 pair_ids=[(q,r['id']) for q in selected for r in candidates[q]]
 pairs=[(queries[q],texts[d]) for q,d in pair_ids]
 benchmarks=[];batch_rows=[];baseline=None;eligible={1,4,8}
 repeats=1 if protocol.get('smoke') else 3
 for rep in range(repeats):
  settings=[1,4,8];random.Random(44+rep).shuffle(settings)
  for batch in settings:
   torch.cuda.reset_peak_memory_stats();t=time.perf_counter()
   try:
    scores,eff,elapsed=timed_score(scorer,pairs,batch)
    benchmarks.append(dict(rep=rep+1,batch=batch,seconds=elapsed,pairs=len(pairs),pairs_per_second=len(pairs)/elapsed,
     effective_batch=eff,peak_allocated_bytes=torch.cuda.max_memory_allocated(),status='ok',error=''))
    batch_rows.extend(dict(rep=rep+1,batch=batch,qid=q,docid=d,score=s['score']) for (q,d),s in zip(pair_ids,scores))
   except torch.cuda.OutOfMemoryError as e:
    eligible.discard(batch);torch.cuda.empty_cache()
    benchmarks.append(dict(rep=rep+1,batch=batch,seconds=time.perf_counter()-t,pairs=len(pairs),pairs_per_second=0,
      effective_batch=0,peak_allocated_bytes=torch.cuda.max_memory_allocated(),status='OOM',error=str(e)[:300]))
   csvout('batches.csv',benchmarks);csvout('scores_por_batch.csv',batch_rows)
   log(f'BATCH {batch}, repeat {rep+1}: {benchmarks[-1]["status"]}')
 ref={(r['qid'],r['docid']):r['score'] for r in batch_rows if r['batch']==1 and r['rep']==1}
 assert len(ref)==len(pair_ids),'Batch1 must be valid to serve as the stability reference'
 stability=[]
 for batch in [1,4,8]:
  valid=batch in eligible and sum(r['batch']==batch and r['status']=='ok' for r in benchmarks)==repeats
  maxdiff=0.;same=True
  for rep in range(1,repeats+1):
   current={(r['qid'],r['docid']):r['score'] for r in batch_rows if r['batch']==batch and r['rep']==rep}
   if len(current)!=len(ref):valid=False;continue
   maxdiff=max(maxdiff,max(abs(current[k]-ref[k]) for k in ref))
   for q in selected:
    ids=[d for qq,d in pair_ids if qq==q]
    a=base.rank(ids,[ref[q,d] for d in ids])[:3];b=base.rank(ids,[current[q,d] for d in ids])[:3]
    same=same and a==b
  accepted=valid and maxdiff<=.001 and same
  stability.append(dict(batch=batch,complete=valid,max_absolute_score_difference=maxdiff,identical_top3=same,accepted=accepted))
 accepted=[r['batch'] for r in stability if r['accepted']]
 if not accepted:chosen=1;reason='No batch passed stability rule; batch1 retained, instability reported'
 else:
  chosen=min(accepted,key=lambda b:np.median([r['seconds'] for r in benchmarks if r['batch']==b and r['status']=='ok']))
  reason='Fastest median time among tested batches satisfying frozen numerical/top3 stability rule'
 csvout('estabilidad_batches.csv',stability);dump('batch_elegido.json',dict(batch=chosen,reason=reason))
 docs=[json.loads(x) for x in (COMMON/'corpus_10000.jsonl').open(encoding='utf-8')]
 retriever=Searcher(docs);engine=Engine(retriever,scorer,queries,candidates,chosen)
 engine.request(qids[0],'fusion',time.perf_counter());engine.request(qids[0],'LLM',time.perf_counter())
 duration_limit=4.5*3600
 def left():return duration_limit-(time.monotonic()-START)
 requests=[];summary=[]
 levels=[1,2,4];random.Random(46).shuffle(levels)
 for level in levels:
  if left()<300:break
  begin=time.perf_counter();completed=[]
  # Submit at most `level` requests: closed-loop load, bounded pending work.
  with cf.ThreadPoolExecutor(max_workers=level) as pool:
   active={};next_i=0
   n_requests=3 if protocol.get('smoke') else 50
   while next_i<n_requests or active:
    while next_i<n_requests and len(active)<level:
     q=qids[next_i%len(qids)];t=time.perf_counter()
     active[pool.submit(engine.request,q,'LLM',t)]=(next_i,q,t);next_i+=1
    done,_=cf.wait(active,return_when=cf.FIRST_COMPLETED)
    for future in done:
     i,q,t=active.pop(future)
     try:r=future.result()
     except Exception as e:r=dict(qid=q,method='LLM',status='error',error=repr(e),seconds=time.perf_counter()-t,
      worker_start_delay_seconds=0,retrieval_seconds=0,union_seconds=0,final_ranking_seconds=0,llm_gpu_queue_seconds=0,
      semantic_gpu_queue_seconds=0,pairs=0,effective_batch=0,top3='')
     r.update(concurrency=level,request=i);completed.append(r);requests.append(r)
  elapsed=time.perf_counter()-begin
  summary.append(dict(concurrency=level,requests=len(completed),errors=sum(r['status']!='ok' for r in completed),
    seconds=elapsed,successful_requests_per_second=sum(r['status']=='ok' for r in completed)/elapsed))
  csvout('concurrencia_solicitudes.csv',requests);csvout('concurrencia_resumen.csv',summary)
  log(f'CONCURRENCY {level} finished')
  if all(r['status']!='ok' for r in completed):raise RuntimeError('All concurrency requests failed; inspect saved errors before retrying')
 dump('politica_cola.json',dict(model_instances=1,gpu_execution_lanes=1,clients=[1,2,4],
  pending_requests_bound='at most client concurrency; closed loop, no overload rejection experiment',
  overlap='CPU lexical search overlaps serialized semantic and LLM GPU operations',
  not_claimed='No independent model replicas, dynamic cross-query batching or open-loop capacity claim'))
 # Alternate methods in shuffled pairs; both execute actual retrieval on every request.
 latency=[];last_llm=10.
 for i in range(2 if protocol.get('smoke') else 1000):
  if left()<max(180,2*last_llm+30):break
  methods=['fusion','LLM'];random.Random(45+i).shuffle(methods)
  for method in methods:
   q=qids[i%len(qids)];t=time.perf_counter()
   try:r=engine.request(q,method,t)
   except Exception as e:r=dict(qid=q,method=method,status='error',error=repr(e),seconds=time.perf_counter()-t,
    worker_start_delay_seconds=0,retrieval_seconds=0,union_seconds=0,final_ranking_seconds=0,llm_gpu_queue_seconds=0,
    semantic_gpu_queue_seconds=0,pairs=0,effective_batch=0,top3='')
   r.update(request=i,concurrency=1);latency.append(r)
   if method=='LLM':last_llm=r['seconds']
  csvout('latencia_solicitudes.csv',latency)
  recent=[r for r in latency[-10:] if r['method']=='LLM']
  if len(recent)>=5 and all(r['status']!='ok' for r in recent):raise RuntimeError('Five successive LLM latency requests failed; stopping instead of repeating invalid work')
  if i%25==0:log(f'LATENCY {i+1}/1000 request pairs; {left()/60:.1f}min budget left')
 dump('rendimiento_completo.json',dict(ok=True,seconds=time.monotonic()-START,latency_requests=len(latency),
  target_each=1000,actual_each={m:sum(r['method']==m for r in latency) for m in ['fusion','LLM']},
  partial_due_to_budget=len(latency)<2000,job=os.environ.get('SLURM_JOB_ID')))
 log('PERFORMANCE_COMPLETE')

def selftest():
 base.selftest()
 assert base.metrics(['x','a','b'],{'a':2})['MRR10']==.5
 assert set(base.rank(['z','a'],[1,1]))=={0,1}
 print('EXPERIMENT_SELF_TEST_OK')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['quality','performance','self-test','recovery-worker'])
 parser.add_argument('--database');parser.add_argument('--source');parser.add_argument('--stop',type=int,default=0)
 args=parser.parse_args()
 if args.stage=='self-test':selftest()
 elif args.stage=='recovery-worker':checkpoint_worker(args.database,args.source,args.stop)
 else:
  try:quality() if args.stage=='quality' else performance()
  except Exception as e:
   OUT.mkdir(exist_ok=True);dump(f'fallo_{args.stage}.json',dict(error=repr(e),traceback=traceback.format_exc(),job=os.environ.get('SLURM_JOB_ID')))
   raise
