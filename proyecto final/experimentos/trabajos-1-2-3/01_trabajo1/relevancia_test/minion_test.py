"""Fixed-alpha MINION test evaluation. All model/metric execution runs under Slurm."""
from pathlib import Path
import os, json, time, hashlib, gc, socket
import numpy as np
import pandas as pd

PREFIX = 'Represent this sentence for searching relevant passages: '
REVISION = 'a5beb1e3e68b9ab74eb54cfd186867f64f240e1a'
ROUTES = ['lex', 'sem', 'fused', 'reranked']
COLORS = dict(lex='#0072B2', sem='#E69F00', fused='#009E73', reranked='#CC79A7')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')

def initialize(root, pilot=False):
    root = Path(root).resolve()
    alpha = json.loads((root/'results/alpha.json').read_text())
    assert alpha['alpha'] == .85 and not alpha['pilot']
    assert alpha['bm25'] == dict(library='bm25s', method='lucene', k1=.9, b=.4,
        stopwords='en', stemmer='english (PyStemmer)', top_k=10)
    assert alpha['semantic'] == dict(query_prefix=PREFIX, max_length=512,
        normalize=True, index='faiss.IndexFlatIP', top_k=10)
    assert alpha['model'] == 'BAAI/bge-base-en-v1.5' and alpha['model_revision'] == REVISION
    assert alpha['normalization'] == 'per-query candidate min-max; constant scores -> 1.0'
    assert alpha['document_tie_break'] == 'ascending document ID (string)'
    assert alpha['encoding'] == 'fp16 forward; CLS pooling; L2 float32; stored float32'
    out = root/('test_pilot' if pilot else 'test_results')
    for p in [out, out/'runs', out/'figs']:
        p.mkdir(exist_ok=True)
    (out/'alpha_usado.json').write_bytes((root/'results/alpha.json').read_bytes())
    (out/'alpha_curve.csv').write_bytes((root/'results/alpha_curve.csv').read_bytes())
    ctx = dict(root=root, out=out, pilot=pilot, alpha=alpha, started=time.monotonic())
    ctx['summary'] = dict(pilot=pilot, alpha=.85, alpha_sha256=sha(out/'alpha_usado.json'),
        node=socket.gethostname(), job_id=os.environ.get('SLURM_JOB_ID'),
        reranker=json.loads((root/'prepared_test.json').read_text())['reranker'], stages={})
    checkpoint(ctx, 'configuration_validated')
    return ctx

def checkpoint(ctx, stage, details=None):
    ctx['summary']['stages'][stage] = dict(elapsed_seconds=time.monotonic()-ctx['started'], details=details)
    ctx['summary']['stage'] = stage
    dump(ctx['out']/'run_summary.json', ctx['summary'])
    print(stage, details if details is not None else '', flush=True)

def load_dataset(ctx, ds):
    data = ctx['root']/'data'/ds
    qr = pd.read_csv(data/'qrels/test.tsv', sep='\t', dtype={'query-id':str,'corpus-id':str})
    qr = qr.rename(columns={'query-id':'query_id','corpus-id':'doc_id','score':'relevance'})
    allq = sorted(set(qr.query_id))
    queries = {}
    for line in (data/'queries.jsonl').open():
        d = json.loads(line)
        if d['_id'] in allq:
            queries[d['_id']] = d['text']
    docs = sorted([json.loads(line) for line in (data/'corpus.jsonl').open()], key=lambda x:x['_id'])
    ids = np.array([d['_id'] for d in docs])
    expected = (57638,648) if ds=='fiqa' else (171332,50)
    assert (len(docs),len(allq)) == expected and len(queries)==expected[1]
    assert len(set(ids))==len(ids) and not qr.duplicated(['query_id','doc_id']).any()
    assert set(qr.doc_id)<=set(ids) and (qr.relevance>=-1).all()
    texts = [d['title']+' '+d['text'] for d in docs]
    audit = dict(corpus=len(docs), test_queries=len(allq), qrels=len(qr),
        positive_qrels=int((qr.relevance>=1).sum()), zero_qrels=int((qr.relevance==0).sum()), negative_unjudged_qrels=int((qr.relevance<0).sum()),
        relevant_queries=int((qr.groupby('query_id').relevance.max()>=1).sum()),
        empty_titles=sum(not d['title'].strip() for d in docs),
        empty_texts=sum(not d['text'].strip() for d in docs),
        duplicate_texts=len(texts)-len(set(texts)),
        corpus_sha256=sha(data/'corpus.jsonl'), qrels_sha256=sha(data/'qrels/test.tsv'))
    counts = json.loads((ctx['out']/'counts.json').read_text()) if (ctx['out']/'counts.json').exists() else {}
    counts[ds] = audit
    dump(ctx['out']/'counts.json', counts)
    qids = allq[:3] if ctx['pilot'] else allq
    qr = qr[qr.query_id.isin(qids)].copy()
    state = dict(ds=ds, docs=docs, ids=ids, texts=texts, qids=qids,
                 queries={q:queries[q] for q in qids}, qrels=qr, audit=audit)
    checkpoint(ctx, ds+'_data_validated', audit)
    return state

def torch_setup():
    import torch
    torch.manual_seed(42); np.random.seed(42)
    torch.cuda.manual_seed_all(42)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(int(os.environ.get('SLURM_CPUS_PER_TASK','8')))
    assert torch.cuda.is_available()
    return torch

def encode(ctx, strings, target):
    if target.exists():
        emb = np.load(target)
        assert emb.shape==(len(strings),768) and emb.dtype==np.float32
        assert np.isfinite(emb).all() and np.allclose(np.linalg.norm(emb,axis=1),1,atol=1e-5)
        return emb
    torch = torch_setup()
    from transformers import AutoTokenizer, AutoModel
    tok=AutoTokenizer.from_pretrained(ctx['root']/'models/bge',local_files_only=True)
    model=AutoModel.from_pretrained(ctx['root']/'models/bge',local_files_only=True,
            torch_dtype=torch.float16,attn_implementation='eager').cuda().eval()
    chunks=[]
    for i in range(0,len(strings),32):
        inputs=tok(strings[i:i+32],padding=True,truncation=True,max_length=512,return_tensors='pt').to('cuda')
        with torch.inference_mode():
            v=torch.nn.functional.normalize(model(**inputs).last_hidden_state[:,0].float(),p=2,dim=1)
        chunks.append(v.cpu().numpy())
        if i%3200==0:
            print('encode',target.name,i,'/',len(strings),flush=True)
    emb=np.ascontiguousarray(np.concatenate(chunks),dtype=np.float32)
    assert np.isfinite(emb).all() and np.allclose(np.linalg.norm(emb,axis=1),1,atol=1e-5)
    tmp=target.with_suffix('.tmp.npy'); np.save(tmp,emb); tmp.replace(target)
    del model,tok,inputs,v; gc.collect(); torch.cuda.empty_cache()
    return emb

def normalize(x):
    return np.ones_like(x) if x.max()==x.min() else (x-x.min())/(x.max()-x.min())

def retrieve(ctx,s):
    ds=s['ds']; out=ctx['out']; root=ctx['root']; cache=root/'cache'
    target=out/f'cands_{ds}_test.parquet'
    if target.exists():
        c=pd.read_parquet(target)
        assert set(c.query_id)==set(s['qids'])
        s['candidates']=c
        checkpoint(ctx,ds+'_candidates_loaded',len(c))
        return c
    import bm25s, Stemmer, faiss
    faiss.omp_set_num_threads(int(os.environ.get('SLURM_CPUS_PER_TASK','8')))
    stem=Stemmer.Stemmer('english')
    index_path=cache/('bm25' if ds=='fiqa' else 'bm25_trec-covid')
    if index_path.exists():
        bm=bm25s.BM25.load(str(index_path),load_corpus=False)
    else:
        bm=bm25s.BM25(k1=.9,b=.4,method='lucene')
        bm.index(bm25s.tokenize(s['texts'],stopwords='en',stemmer=stem))
        bm.save(str(index_path))
    checkpoint(ctx,ds+'_bm25_ready')
    n=256 if ctx['pilot'] and ds!='fiqa' else len(s['docs'])
    tag='_pilot' if ctx['pilot'] else ''
    embname=f'emb_{ds}.npy' if n==len(s['docs']) else f'emb_{ds}_pilot.npy'
    emb=encode(ctx,s['texts'][:n],cache/embname)
    qe=encode(ctx,[PREFIX+s['queries'][q] for q in s['qids']],cache/f'emb_{ds}_test{tag}.npy')
    dense=faiss.IndexFlatIP(768); dense.add(emb)
    checkpoint(ctx,ds+'_embeddings_ready',dict(documents=n,queries=len(qe)))
    rows=[]
    for qi,qid in enumerate(s['qids']):
        tokens=bm25s.tokenize([s['queries'][qid]],stopwords='en',stemmer=stem,return_ids=False,show_progress=False)[0]
        lex=np.asarray(bm.get_scores(tokens)); lt=np.argsort(-lex,kind='stable')[:10]
        distances,positions=dense.search(qe[qi:qi+1],n)
        scores=np.empty(n,dtype=np.float32); scores[positions[0]]=distances[0]
        st=np.argsort(-scores,kind='stable')[:10]
        cand=sorted(set(lt.tolist())|set(st.tolist()))
        extra=[i for i in cand if i>=n]
        ev=encode(ctx,[s['texts'][i] for i in extra],cache/f'{ds}_extra_{qid}.npy') if extra else []
        extra_map=dict(zip(extra,ev))
        lr=lex[cand].astype(np.float64)
        sr=np.array([np.dot(emb[i] if i<n else extra_map[i],qe[qi]) for i in cand],dtype=np.float64)
        ln,sn=normalize(lr),normalize(sr)
        lrank={i:r+1 for r,i in enumerate(lt)}; srank={i:r+1 for r,i in enumerate(st)}
        for j,di in enumerate(cand):
            rows.append(dict(query_id=qid,doc_id=s['ids'][di],corpus_index=int(di),
                lex_raw=float(lr[j]),sem_raw=float(sr[j]),lex_norm=float(ln[j]),sem_norm=float(sn[j]),
                lex_rank=lrank.get(di,0),sem_rank=srank.get(di,0),fused_score=float((1-ctx['alpha']['alpha'])*ln[j]+ctx['alpha']['alpha']*sn[j])))
        if qi%50==0: print('candidates',ds,qi,'/',len(s['qids']),flush=True)
    c=pd.DataFrame(rows)
    assert not c.duplicated(['query_id','doc_id']).any()
    assert c.groupby('query_id').size().between(10,20).all()
    assert np.isfinite(c[['lex_raw','sem_raw','lex_norm','sem_norm']].to_numpy()).all()
    c.to_parquet(target,index=False); s['candidates']=c
    del emb,qe,dense,bm; gc.collect()
    checkpoint(ctx,ds+'_candidate_scores_saved',len(c))
    return c

def rerank(ctx,s):
    c=s['candidates']; ds=s['ds']
    if 'ce_score' not in c:
        torch=torch_setup()
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        tok=AutoTokenizer.from_pretrained(ctx['root']/'models/reranker',local_files_only=True)
        model=AutoModelForSequenceClassification.from_pretrained(ctx['root']/'models/reranker',
            local_files_only=True,torch_dtype=torch.float32,attn_implementation='eager').cuda().eval()
        c=c.copy(); c['ce_score']=np.nan
        for qi,(qid,g) in enumerate(c.groupby('query_id',sort=True)):
            g=g.sort_values(['fused_score','doc_id'],ascending=[False,True],kind='stable')
            texts=[s['texts'][i] for i in g.corpus_index]
            inputs=tok([s['queries'][qid]]*len(g),texts,padding=True,truncation=True,
                        max_length=512,return_tensors='pt').to('cuda')
            with torch.inference_mode():
                scores=model(**inputs).logits.flatten().cpu().numpy()
            c.loc[g.index,'ce_score']=scores
            if qi%100==0: print('rerank',ds,qi,'/',len(s['qids']),flush=True)
        assert np.isfinite(c.ce_score).all()
        c.to_parquet(ctx['out']/f'cands_{ds}_test.parquet',index=False)
        del model,tok,inputs,scores; gc.collect(); torch.cuda.empty_cache()
    runs={r:{} for r in ROUTES}
    for qid,g in c.groupby('query_id',sort=True):
        fused=g.sort_values(['fused_score','doc_id'],ascending=[False,True],kind='stable')
        ce=fused.sort_values('ce_score',ascending=False,kind='stable')
        runs['fused'][qid]=fused.doc_id.tolist(); runs['reranked'][qid]=ce.doc_id.tolist()
        for route in ['lex','sem']:
            part=g[g[route+'_rank']>0].sort_values(route+'_rank')
            runs[route][qid]=part.doc_id.tolist()
            assert len(part)==10
        assert len(fused)<=20 and set(fused.doc_id)==set(ce.doc_id)
    for route,run in runs.items():
        lines=[f'{q} Q0 {d} {rank} {len(docs)-rank+1} minion_{route}'
               for q,docs in run.items() for rank,d in enumerate(docs,1)]
        (ctx['out']/'runs'/f'{ds}_{route}.trec').write_text('\n'.join(lines)+'\n')
    s['candidates']=c; s['runs']=runs
    checkpoint(ctx,ds+'_reranked_same_candidates',dict(queries=len(s['qids']),candidates=len(c)))
    return runs

def per_query(s,run):
    import ir_measures as irm
    qr=s['qrels']; qids=s['qids']
    measures=[irm.P(rel=1)@3,irm.nDCG@3,irm.RR(rel=1)@10,irm.R(rel=1)@20]
    names=['precision_at_3','ndcg_at_3','mrr_at_10','recall_at_20']
    runrows=[dict(query_id=q,doc_id=d,score=float(len(docs)-i)) for q,docs in run.items() for i,d in enumerate(docs)]
    rdf=pd.DataFrame(runrows,columns=['query_id','doc_id','score'])
    result=pd.DataFrame(0.,index=pd.Index(qids,name='query_id'),columns=names)
    for metric in irm.iter_calc(measures,qr,rdf):
        result.loc[metric.query_id,names[measures.index(metric.measure)]]=metric.value
    rels={q:dict(zip(g.doc_id,g.relevance)) for q,g in qr.groupby('query_id')}
    for q in qids:
        rel=rels[q]; docs=run.get(q,[]); grades=[max(0,rel.get(d,0)) for d in docs]
        p=sum(g>=1 for g in grades[:3])/3
        ideal=sorted([max(0,v) for v in rel.values()],reverse=True)[:3]
        idcg=sum(g/np.log2(i+2) for i,g in enumerate(ideal))
        ndcg=sum(g/np.log2(i+2) for i,g in enumerate(grades[:3]))/idcg if idcg else 0.
        rr=next((1/(i+1) for i,g in enumerate(grades[:10]) if g>=1),0.)
        denom=sum(g>=1 for g in rel.values())
        recall=sum(g>=1 for g in grades[:20])/denom if denom else 0.
        assert np.allclose(result.loc[q].to_numpy(),[p,ndcg,rr,recall],atol=1e-12)
    return result

def evaluate(ctx,s):
    ds=s['ds']; qids=s['qids']; qr=s['qrels']; run=s['runs']
    metrics=[]; judged=[]; condensed=[]; per=[]; boot=[]; cis=[]
    arrays={}; c_arrays={}; rels={q:dict(zip(g.doc_id,g.relevance)) for q,g in qr.groupby('query_id')}
    for route in ROUTES:
        a=per_query(s,run[route]); arrays[route]=a
        positive=qr.groupby('query_id').relevance.max().reindex(qids)>=1
        row=dict(dataset=ds,route=route,n_queries=len(qids),**a.mean().to_dict())
        row['recall_at_20']=float(a.loc[positive,'recall_at_20'].mean()) if route=='fused' else np.nan
        row['recall_queries']=int(positive.sum()) if route=='fused' else np.nan
        metrics.append(row)
        for q,values in a.iterrows():
            per.append(dict(dataset=ds,route=route,query_id=q,**values.to_dict()))
        j=np.array([sum(d in rels[q] for d in run[route][q][:10])/10 for q in qids])
        judged.append(dict(dataset=ds,route=route,judged_at_10=float(j.mean()),judged_at_10_percent=float(100*j.mean())))
        crun={q:[d for d in run[route][q] if d in rels[q]] for q in qids}
        ca=per_query(s,crun); c_arrays[route]=ca
        condensed.append(dict(dataset=ds,route=route,precision_at_3=float(ca.precision_at_3.mean()),ndcg_at_3=float(ca.ndcg_at_3.mean())))
    rng=np.random.default_rng(42)
    sample=rng.integers(0,len(qids),size=(10000,len(qids)))
    delta=(arrays['reranked'].precision_at_3-arrays['fused'].precision_at_3).to_numpy()
    samples=delta[sample].mean(axis=1)
    low,high=np.percentile(samples,[2.5,97.5])
    condensed_delta=float((c_arrays['reranked'].precision_at_3-c_arrays['fused'].precision_at_3).mean())
    bootrow=dict(dataset=ds,n_queries=len(qids),resamples=10000,seed=42,delta_precision_at_3=float(delta.mean()),
                 ci_95_low=float(low),ci_95_high=float(high),condensed_delta_precision_at_3=condensed_delta,
                 delta_sign_preserved=bool(np.sign(round(float(delta.mean()),12))==np.sign(round(condensed_delta,12))))
    for route,a in arrays.items():
        for metric in ['precision_at_3','ndcg_at_3','mrr_at_10']:
            vals=a[metric].to_numpy(); bs=vals[sample].mean(axis=1); lo,hi=np.percentile(bs,[2.5,97.5])
            cis.append(dict(dataset=ds,route=route,metric=metric,mean=float(vals.mean()),ci_95_low=float(lo),ci_95_high=float(hi)))
    s.update(arrays=arrays,condensed_arrays=c_arrays,bootstrap=bootrow,bootstrap_samples=samples)
    for filename,rows in [('metrics.csv',metrics),('judged.csv',judged),('condensed.csv',condensed),
                         ('per_query_metrics.csv',per),('metric_ci.csv',cis),('bootstrap.csv',[bootrow])]:
        path=ctx['out']/filename
        existing=pd.read_csv(path,dtype={'query_id':str}) if path.exists() else pd.DataFrame()
        if len(existing): existing=existing[existing.dataset!=ds]
        pd.concat([existing,pd.DataFrame(rows)],ignore_index=True).to_csv(path,index=False)
    pd.DataFrame(dict(replicate=np.arange(10000),delta_precision_at_3=samples)).to_csv(ctx['out']/f'bootstrap_samples_{ds}.csv',index=False)
    checkpoint(ctx,ds+'_metrics_bootstrap_complete',bootrow)
    return bootrow

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--pilot',action='store_true'); p.add_argument('--root',type=Path,default=Path(__file__).parent)
    a=p.parse_args(); ctx=initialize(a.root,a.pilot)
    for ds in ['fiqa','trec-covid']:
        s=load_dataset(ctx,ds); retrieve(ctx,s); rerank(ctx,s); evaluate(ctx,s)
        del s; gc.collect()
    checkpoint(ctx,'PILOT_PASSED' if a.pilot else 'COMPUTE_COMPLETE')

if __name__=='__main__': main()



