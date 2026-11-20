"""Final independent artifact checks, run with Slurm on Khipu."""
from pathlib import Path
import os,json,hashlib,shutil
import numpy as np
import pandas as pd
import nbformat
from PIL import Image,ImageOps,ImageDraw

root=Path(__file__).resolve().parent; out=root/'test_results'
alpha=json.loads((out/'alpha_usado.json').read_text())
assert alpha['alpha']==.85 and (out/'alpha_usado.json').read_bytes()==(root/'results/alpha.json').read_bytes()
summary=json.loads((out/'run_summary.json').read_text()); assert summary['stage']=='COMPLETE_VERIFIED'
nb=nbformat.read(out/'trabajo1_relevancia.ipynb',as_version=4)
code=[c for c in nb.cells if c.cell_type=='code']
assert all(c.execution_count is not None for c in code)
assert not [o for c in code for o in c.outputs if o.output_type=='error']
assert sum('image/png' in o.get('data',{}) for c in code for o in c.outputs)==15
boot=pd.read_csv(out/'bootstrap.csv'); counts=json.loads((out/'counts.json').read_text())
report={'passed':True,'alpha':.85,'audit_job_id':os.environ.get('SLURM_JOB_ID'),
        'notebook_code_cells':len(code),'notebook_errors':0,'inline_figures':15,'datasets':{}}
for ds,nq,nd in [('fiqa',648,57638),('trec-covid',50,171332)]:
    assert counts[ds]['test_queries']==nq and counts[ds]['corpus']==nd
    c=pd.read_parquet(out/f'cands_{ds}_test.parquet')
    assert c.query_id.nunique()==nq and not c.duplicated(['query_id','doc_id']).any()
    qr=pd.read_csv(root/'data'/ds/'qrels/test.tsv',sep='\t',dtype={'query-id':str,'corpus-id':str})
    negatives=set(zip(qr.loc[qr.score<0,'query-id'],qr.loc[qr.score<0,'corpus-id']))
    negative_hits=[]
    runs={}
    for route in ['lex','sem','fused','reranked']:
        r=pd.read_csv(out/'runs'/f'{ds}_{route}.trec',sep=r'\s+',header=None,
                      names=['query_id','q0','doc_id','rank','score','tag'],dtype={'query_id':str,'doc_id':str})
        assert r.query_id.nunique()==nq and not r.duplicated(['query_id','doc_id']).any()
        runs[route]={q:g.sort_values('rank').doc_id.tolist() for q,g in r.groupby('query_id')}
        for q,g in r.groupby('query_id'):
            assert g['rank'].tolist()==list(range(1,len(g)+1))
    for q,g in c.groupby('query_id',sort=True):
        assert 10<=len(g)<=20 and (g.lex_rank>0).sum()==(g.sem_rank>0).sum()==10
        for prefix in ['lex','sem']:
            raw=g[prefix+'_raw'].to_numpy(); expected=np.ones_like(raw) if raw.max()==raw.min() else (raw-raw.min())/(raw.max()-raw.min())
            assert np.allclose(expected,g[prefix+'_norm'],atol=1e-14)
        expected=(1-alpha['alpha'])*g.lex_norm+alpha['alpha']*g.sem_norm
        assert np.allclose(expected,g.fused_score,atol=1e-14)
        f=g.sort_values(['fused_score','doc_id'],ascending=[False,True],kind='stable')
        r=f.sort_values('ce_score',ascending=False,kind='stable')
        assert f.doc_id.tolist()==runs['fused'][q]
        assert r.doc_id.tolist()==runs['reranked'][q]
        assert set(r.doc_id)==set(f.doc_id)
        for d in g.doc_id:
            if (q,d) in negatives: negative_hits.append([q,d])
    # Audit whether literal qrel membership differs from grade >= 0 judgment.
    print(ds, 'explicit -1 judgments retrieved:', negative_hits)
    pq=pd.read_csv(out/'per_query_metrics.csv',dtype={'query_id':str})
    p=pq[pq.dataset==ds].pivot(index='query_id',columns='route',values='precision_at_3').sort_index()
    delta=(p.reranked-p.fused).to_numpy()
    rng=np.random.default_rng(42); indices=rng.integers(0,nq,size=(10000,nq))
    samples=delta[indices].mean(axis=1)
    stored=pd.read_csv(out/f'bootstrap_samples_{ds}.csv').delta_precision_at_3.to_numpy()
    assert len(stored)==10000 and np.allclose(samples,stored,atol=1e-14)
    low,high=np.percentile(samples,[2.5,97.5]); b=boot[boot.dataset==ds].iloc[0]
    assert np.allclose([delta.mean(),low,high],[b.delta_precision_at_3,b.ci_95_low,b.ci_95_high],atol=1e-14)
    report['datasets'][ds]=dict(queries=nq,documents=nd,candidate_rows=len(c),
        explicit_negative_qrels=len(negatives),negative_qrels_retrieved=negative_hits, literal_and_nonnegative_judged_definitions_identical=not bool(negative_hits),
        identical_candidate_sets=True,normalization_verified=True,ranking_ties_verified=True,
        bootstrap_replicates=10000,bootstrap_verified=True)
figs=sorted((out/'figs').glob('*.png')); assert len(figs)==15
thumbs=[]
for p in figs:
    im=Image.open(p); assert min(im.size)>500
    assert abs(im.info['dpi'][0]-200)<1
    thumb=ImageOps.contain(im.convert('RGB'),(600,380))
    tile=Image.new('RGB',(620,420),'white'); tile.paste(thumb,((620-thumb.width)//2,30))
    ImageDraw.Draw(tile).text((10,7),p.name,fill='black'); thumbs.append(tile)
sheet=Image.new('RGB',(620*3,420*5),'#DDDDDD')
for i,t in enumerate(thumbs): sheet.paste(t,((i%3)*620,(i//3)*420))
sheet.save(out/'figures_contact_sheet.jpg',quality=92)
(out/'final_verification.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copy2(__file__,out/'audit_test_outputs.py')
print(json.dumps(report,indent=2),flush=True)

