"""MINION complementary CPU analyses; fixed alpha=.85, RRF k=60, dev-only gates."""
from pathlib import Path
import argparse,json,hashlib,os,socket,time,importlib.metadata as metadata
import numpy as np
import pandas as pd
import ir_measures as irm

METRICS=['precision_at_3','ndcg_at_3']
DATASETS=['fiqa','trec-covid']
TARGETS=[.25,.50,.75]
RRF_K=60

def dump(path,value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def sources(project):
    files=[project/'results/alpha.json',project/'results/alpha_curve.csv',
           project/'results/cands_fiqa_dev.parquet',project/'test_results/alpha_usado.json',
           project/'test_results/per_query_metrics.csv']
    for ds in DATASETS:
        files.extend([project/'test_results'/f'cands_{ds}_test.parquet',project/'data'/ds/'qrels/test.tsv'])
        files.extend(project/'test_results/runs'/f'{ds}_{r}.trec' for r in ['lex','sem','fused','reranked'])
    for p in files: assert p.is_file(), f'Missing input: {p}'
    return {str(p):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}

def load_run(path):
    t=pd.read_csv(path,sep=r'\s+',header=None,names=['query_id','q0','doc_id','rank','score','tag'],
                  dtype={'query_id':str,'doc_id':str})
    assert not t.duplicated(['query_id','doc_id']).any()
    result={}
    for q,g in t.groupby('query_id',sort=True):
        g=g.sort_values('rank',kind='stable')
        assert g['rank'].tolist()==list(range(1,len(g)+1)), (path,q)
        result[q]=g.doc_id.tolist()
    return result

def fused_groups(candidates,alpha):
    groups={}; gaps={}; eligible={}
    for q,g in candidates.groupby('query_id',sort=True):
        g=g.copy(); g['computed_fused']=(1-alpha)*g.lex_norm+alpha*g.sem_norm
        if 'fused_score' in g:
            assert np.allclose(g.computed_fused,g.fused_score,rtol=0,atol=1e-14)
        g=g.sort_values(['computed_fused','doc_id'],ascending=[False,True],kind='stable')
        assert len(g.doc_id)==len(set(g.doc_id))
        groups[q]=g
        eligible[q]=len(g)>=4
        gaps[q]=float(g.computed_fused.iloc[2]-g.computed_fused.iloc[3]) if len(g)>=4 else None
        assert gaps[q] is None or gaps[q]>=0
    return groups,gaps,eligible

def freeze_thresholds(project,folder,alpha):
    path=project/'results/cands_fiqa_dev.parquet'
    c=pd.read_parquet(path)
    groups,gaps,eligible=fused_groups(c,alpha)
    assert len(groups)==500
    rows=pd.DataFrame([dict(query_id=q,candidates=len(groups[q]),eligible=eligible[q],gap_3_4=gaps[q]) for q in groups])
    values=rows.loc[rows.eligible,'gap_3_4'].to_numpy()
    thresholds=[]
    for rate in TARGETS:
        # Quantiles are fixed using only development margins. Include all dev
        # queries in the target denominator; in this saved corpus every query is eligible.
        quantile=min(1.,rate*len(rows)/len(values))
        threshold=float(np.quantile(values,quantile,method='linear'))
        invoked=rows.eligible & (rows.gap_3_4<=threshold)
        thresholds.append(dict(target_rate=rate,threshold=threshold,dev_invocations=int(invoked.sum()),
            dev_queries=len(rows),dev_actual_rate=float(invoked.mean()),quantile=quantile))
    fixed=dict(analysis='complementary',alpha=alpha,training_split='FiQA-dev',primary_target_rate=.5,
        rule='rerank iff n_candidates >= 4 and fused_score_rank3 - fused_score_rank4 <= threshold',
        quantile_method='numpy.quantile(method=linear)',threshold_ties='invoke all gaps <= threshold; report actual rates',
        source_path=str(path),source_sha256=sha(path),thresholds=thresholds)
    dump(folder/'thresholds_fixed.json',fixed)
    rows.to_csv(folder/'dev_margins.csv',index=False)
    return fixed

def load_dataset(project,ds,alpha):
    c=pd.read_parquet(project/'test_results'/f'cands_{ds}_test.parquet')
    groups,gaps,eligible=fused_groups(c,alpha)
    runs={r:load_run(project/'test_results/runs'/f'{ds}_{r}.trec') for r in ['lex','sem','fused','reranked']}
    qids=sorted(groups)
    assert len(qids)==(648 if ds=='fiqa' else 50)
    assert all(set(runs[r])==set(qids) for r in runs)
    rrf={}; rows=[]; score_rows=[]
    for q in qids:
        lexical,semantic=runs['lex'][q],runs['sem'][q]
        assert len(lexical)==len(semantic)==10
        union=set(lexical)|set(semantic)
        assert union==set(groups[q].doc_id)==set(runs['fused'][q])==set(runs['reranked'][q])
        assert groups[q].doc_id.tolist()==runs['fused'][q]
        score={d:0. for d in union}
        for docs in [lexical,semantic]:
            for rank,d in enumerate(docs,1): score[d]+=1./(RRF_K+rank)
        rrf[q]=sorted(union,key=lambda d:(-score[d],d))
        assert set(rrf[q])==union
        for rank,d in enumerate(rrf[q],1):
            score_rows.append(dict(dataset=ds,query_id=q,doc_id=d,rrf_rank=rank,rrf_score=score[d],
                lexical_rank=lexical.index(d)+1 if d in lexical else 0,
                semantic_rank=semantic.index(d)+1 if d in semantic else 0))
        rows.append(dict(dataset=ds,query_id=q,candidate_count=len(union),candidate_sets_equal=True,
                         gap_3_4=gaps[q],eligible=eligible[q]))
    qr=pd.read_csv(project/'data'/ds/'qrels/test.tsv',sep='\t',dtype={'query-id':str,'corpus-id':str})
    qr=qr.rename(columns={'query-id':'query_id','corpus-id':'doc_id','score':'relevance'})
    assert set(qr.query_id)==set(qids)
    runs['rrf']=rrf
    return dict(ds=ds,qids=qids,runs=runs,qrels=qr,decisions=pd.DataFrame(rows),rrf_scores=pd.DataFrame(score_rows))

def metrics_for_run(s,run):
    measures=[irm.P(rel=1)@3,irm.nDCG@3]
    qids=sorted(run)
    qr=s['qrels'][s['qrels'].query_id.isin(qids)]
    rows=[dict(query_id=q,doc_id=d,score=float(len(docs)-r)) for q,docs in run.items() for r,d in enumerate(docs)]
    result=pd.DataFrame(0.,index=pd.Index(qids,name='query_id'),columns=METRICS)
    for v in irm.iter_calc(measures,qr,pd.DataFrame(rows)):
        result.loc[v.query_id,METRICS[measures.index(v.measure)]]=v.value
    # Independent verification includes original graded nDCG; -1 is unjudged.
    relevant={q:dict(zip(g.doc_id,g.relevance)) for q,g in qr.groupby('query_id')}
    for q in qids:
        rel=relevant[q]; grades=[max(0,rel.get(d,0)) for d in run[q][:3]]
        ideal=sorted([max(0,v) for v in rel.values()],reverse=True)[:3]
        idcg=sum(v/np.log2(i+2) for i,v in enumerate(ideal))
        expected=[sum(v>=1 for v in grades)/3,
                  sum(v/np.log2(i+2) for i,v in enumerate(grades))/idcg if idcg else 0.]
        assert np.allclose(result.loc[q],expected,atol=1e-12)
    return result

def comparison(dataset,label,variant,baseline,bootstrap_indices):
    rows=[]
    for metric in METRICS:
        delta=(variant[metric]-baseline[metric]).to_numpy()
        samples=delta[bootstrap_indices].mean(axis=1)
        lo,hi=np.percentile(samples,[2.5,97.5])
        rows.append(dict(dataset=dataset,comparison=label,metric=metric,
            mean_difference=float(delta.mean()),ci_95_low=float(lo),ci_95_high=float(hi),
            resamples=len(samples),paired_queries=len(delta)))
    return rows

def subset_metrics(frame,qids): return frame.loc[qids,METRICS]

def analyze(s,fixed,out,smoke=False):
    ds=s['ds']; qids=s['qids'][:5] if smoke else s['qids']; n=len(qids)
    reps=3 if smoke else 100; nboot=100 if smoke else 10000
    stats={r:metrics_for_run(s,{q:s['runs'][r][q] for q in qids}) for r in ['fused','reranked','rrf']}
    fused,full=stats['fused'],stats['reranked']
    original=pd.read_csv(PROJECT/'test_results/per_query_metrics.csv',dtype={'query_id':str})
    for route,current in [('fused',fused),('reranked',full)]:
        prior=original[(original.dataset==ds)&(original.route==route)].set_index('query_id').loc[qids,METRICS]
        assert np.allclose(prior,current,atol=1e-12)
    bootstrap_seed=420+DATASETS.index(ds)
    indices=np.random.default_rng(bootstrap_seed).integers(0,n,size=(nboot,n))
    rrf_summary=[]; rrf_per=[]
    for name,a in [('convex',fused),('rrf',stats['rrf'])]:
        rrf_summary.append(dict(dataset=ds,method=name,rrf_k=60,alpha=.85,n_queries=n,**a.mean().to_dict()))
        rrf_per.extend(dict(dataset=ds,query_id=q,method=name,**row.to_dict()) for q,row in a.iterrows())
    rrf_compare=comparison(ds,'rrf_minus_convex',stats['rrf'],fused,indices)
    selective_summary=[]; selective_per=[]; differences=[]; random_draws=[]; random_masks=[]; seed_rows=[]
    decision=s['decisions'].set_index('query_id').loc[qids].copy()
    for name,a,rate in [('fused',fused,0.),('full_reranking',full,1.)]:
        selective_summary.append(dict(dataset=ds,policy=name,target_rate=np.nan,threshold=np.nan,
            invocation_count=int(rate*n),actual_invocation_rate=rate,primary=False,**a.mean().to_dict()))
        selective_per.extend(dict(dataset=ds,query_id=q,policy=name,target_rate=np.nan,invocation_probability=rate,
                                  **row.to_dict()) for q,row in a.iterrows())
    differences.extend(comparison(ds,'full_reranking_minus_fused',full,fused,indices))
    for j,t in enumerate(fixed['thresholds']):
        target=t['target_rate']; threshold=t['threshold']
        invoke=(decision.eligible & (decision.gap_3_4<=threshold)).to_numpy()
        k=int(invoke.sum()); selected=fused.copy()
        selected.loc[invoke,METRICS]=full.loc[invoke,METRICS].to_numpy()
        assert not (invoke & ~decision.eligible.to_numpy()).any()
        masks=[]
        for rep in range(reps):
            seed=42000+DATASETS.index(ds)*10000+j*1000+rep
            mask=np.zeros(n,dtype=bool)
            # All saved test queries have >=4 candidates. Restrict the control
            # to eligible queries as well, preserving the mandatory fallback.
            eligible_positions=np.flatnonzero(decision.eligible.to_numpy())
            if k: mask[np.random.default_rng(seed).choice(eligible_positions,size=k,replace=False)]=True
            assert int(mask.sum())==k
            masks.append(mask)
            values=fused.to_numpy()+mask[:,None]*(full.to_numpy()-fused.to_numpy())
            random_draws.append(dict(dataset=ds,target_rate=target,replicate=rep,seed=seed,
                invocations=k,actual_invocation_rate=k/n,**dict(zip(METRICS,values.mean(axis=0)))))
            seed_rows.append(dict(dataset=ds,target_rate=target,replicate=rep,seed=seed))
            random_masks.extend(dict(dataset=ds,target_rate=target,replicate=rep,seed=seed,query_id=q,invoked=bool(v)) for q,v in zip(qids,mask))
        probability=np.mean(masks,axis=0)
        random_mean=pd.DataFrame(fused.to_numpy()+probability[:,None]*(full.to_numpy()-fused.to_numpy()),index=fused.index,columns=METRICS)
        assert np.isclose(probability.sum(),k)
        for policy,a,probs in [('selective',selected,invoke.astype(float)),('random_mean_100',random_mean,probability)]:
            selective_summary.append(dict(dataset=ds,policy=policy,target_rate=target,threshold=threshold,
                invocation_count=k,actual_invocation_rate=k/n,primary=target==.5,**a.mean().to_dict()))
            selective_per.extend(dict(dataset=ds,query_id=q,policy=policy,target_rate=target,
                invocation_probability=float(probs[i]),**row.to_dict()) for i,(q,row) in enumerate(a.iterrows()))
        for label,base in [('selective_minus_fused',fused),('selective_minus_random_mean_100',random_mean),
                           ('random_mean_100_minus_fused',fused)]:
            variant=random_mean if label=='random_mean_100_minus_fused' else selected
            d=comparison(ds,label,variant,base,indices)
            for row in d: row.update(target_rate=target,primary=target==.5)
            differences.extend(d)
        decision[f'invoke_target_{int(target*100)}']=invoke
    tables=dict(rrf_metrics=rrf_summary,rrf_per_query=rrf_per,rrf_paired_differences=rrf_compare,
        selective_metrics=selective_summary,selective_per_query=selective_per,
        selective_paired_differences=differences,random_draw_metrics=random_draws,random_decisions=random_masks,random_seeds=seed_rows)
    for name,rows in tables.items(): pd.DataFrame(rows).to_csv(out/f'{name}_{ds}.csv',index=False)
    decision.reset_index().to_csv(out/f'selective_decisions_{ds}.csv',index=False)
    s['rrf_scores'].to_csv(out/f'rrf_scores_{ds}.csv',index=False)
    dump(out/f'verification_{ds}.json',dict(passed=True,queries=n,all_query_candidate_sets_equal=True,
        cached_metrics_match=True,bootstrap_seed=bootstrap_seed,bootstrap_resamples=nboot,
        random_repetitions=reps,random_exact_invocation_counts=True))
    print('DATASET_VERIFIED',ds,n,flush=True)

def make_figures(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
    for i,ds in enumerate(DATASETS):
        m=pd.read_csv(out/f'rrf_metrics_{ds}.csv').set_index('method')
        d=pd.read_csv(out/f'rrf_paired_differences_{ds}.csv').set_index('metric')
        for j,metric in enumerate(METRICS):
            ax=axes[i,j]; vals=m.loc[['convex','rrf'],metric].to_numpy()
            ax.bar(['Convexa α=0,85','RRF k=60'],vals,color=['#009E73','#0072B2'])
            for x,v in enumerate(vals): ax.text(x,v+.015,f'{v:.4f}',ha='center')
            a=d.loc[metric]
            ax.set(ylim=(0,1.15),ylabel='Métrica (0–1)',title=f"{ds} · {metric}\nΔ RRF−convexa {a.mean_difference:+.4f}; IC 95 % [{a.ci_95_low:+.4f}, {a.ci_95_high:+.4f}]")
            ax.grid(axis='y',alpha=.2)
    fig.suptitle('MINION · análisis complementario 1 · métodos de fusión sin cross-encoder',fontsize=14)
    fig.savefig(out/'experimento_1_fusiones.png',dpi=200); plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
    for i,ds in enumerate(DATASETS):
        m=pd.read_csv(out/f'selective_metrics_{ds}.csv')
        for j,metric in enumerate(METRICS):
            ax=axes[i,j]
            ax.axhline(float(m.loc[m.policy=='fused',metric].iloc[0]),color='#009E73',ls='--',label='Fusión sola')
            ax.axhline(float(m.loc[m.policy=='full_reranking',metric].iloc[0]),color='#CC79A7',ls=':',label='Reranking completo')
            for policy,color,name in [('selective','#0072B2','Selectivo por margen'),('random_mean_100','#E69F00','Aleatorio (media de 100)')]:
                sub=m[m.policy==policy].sort_values('target_rate')
                ax.plot(100*sub.actual_invocation_rate,sub[metric],'o-',color=color,label=name)
                if policy=='selective':
                    for _,r in sub.iterrows(): ax.annotate(f"meta {r.target_rate:.0%}",(100*r.actual_invocation_rate,r[metric]),xytext=(4,8),textcoords='offset points',fontsize=9)
                    p=sub[sub.target_rate==.5].iloc[0]
                    ax.scatter([100*p.actual_invocation_rate],[p[metric]],marker='*',s=180,color=color,edgecolors='black',zorder=5,label='Principal: meta 50 %')
            ax.set(xlabel='Invocaciones simuladas reales (%)',ylabel='Métrica (0–1)',xlim=(-3,103),title=f'{ds} · {metric}')
            ax.legend(fontsize=7,loc='best'); ax.grid(alpha=.2)
    fig.suptitle('MINION · análisis complementario 2 · relevancia e invocaciones (sin medir latencia)',fontsize=14)
    fig.savefig(out/'experimento_2_selectivo.png',dpi=200); plt.close(fig)

def synthetic_checks():
    # RRF missing-route contribution is zero; exact ties use ascending ID.
    scores={'b':1/(60+1),'a':1/(60+1),'c':1/(60+2)+1/(60+2)}
    assert sorted(scores,key=lambda d:(-scores[d],d))==['c','a','b']
    c=pd.DataFrame(dict(query_id=['q']*3,doc_id=['c','b','a'],lex_norm=[0.,.5,1.],sem_norm=[0.,.5,1.]))
    g,gaps,eligible=fused_groups(c,.85)
    assert not eligible['q'] and gaps['q'] is None and g['q'].doc_id.tolist()==['a','b','c']

def main():
    global PROJECT
    parser=argparse.ArgumentParser(); parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args(); folder=Path(__file__).resolve().parent; PROJECT=folder.parent
    out=folder/('preflight' if args.smoke else 'resultados'); out.mkdir(exist_ok=True)
    started=time.monotonic(); synthetic_checks()
    inputs=sources(PROJECT)
    alpha=json.loads((PROJECT/'results/alpha.json').read_text())
    assert alpha['alpha']==.85 and not alpha['pilot']
    assert (PROJECT/'results/alpha.json').read_bytes()==(PROJECT/'test_results/alpha_usado.json').read_bytes()
    code_hash=sha(__file__)
    if args.smoke:
        fixed=freeze_thresholds(PROJECT,folder,alpha['alpha'])
    else:
        preflight=json.loads((folder/'preflight_verified.json').read_text())
        assert preflight['passed'] and preflight['script_sha256']==code_hash
        assert preflight['inputs']==inputs, 'Input changes after preflight'
        assert preflight['thresholds_sha256']==sha(folder/'thresholds_fixed.json')
        fixed=json.loads((folder/'thresholds_fixed.json').read_text())
        assert fixed['source_sha256']==sha(PROJECT/'results/cands_fiqa_dev.parquet')
    dump(out/'inputs_manifest.json',inputs)
    dump(out/'thresholds_fixed.json',fixed)
    dump(out/'alpha_usado.json',alpha)
    for ds in DATASETS:
        state=load_dataset(PROJECT,ds,alpha['alpha'])
        analyze(state,fixed,out,args.smoke)
    make_figures(out)
    versions={p:metadata.version(p) for p in ['numpy','pandas','ir_measures','matplotlib','pyarrow']}
    summary=dict(analysis_type='complementary',passed=True,smoke=args.smoke,
        alpha=.85,rrf_k=60,thresholds_source='FiQA-dev only; frozen before test evaluation',
        primary_target_rate=.5,thresholds_sha256=sha(folder/'thresholds_fixed.json'),
        script_sha256=code_hash,inputs=inputs,versions=versions,
        bootstrap_seeds={ds:420+i for i,ds in enumerate(DATASETS)},
        bootstrap_resamples=100 if args.smoke else 10000,
        random_repetitions=3 if args.smoke else 100,
        random_seed_formula='42000 + dataset_index*10000 + target_index*1000 + replicate_index',
        paired_random_comparison='query bootstrap conditional on the recorded average of 100 fixed random selections',
        latencies_measured=False,model_inference_executed=False,
        node=socket.gethostname(),slurm_job_id=os.environ.get('SLURM_JOB_ID'),elapsed_seconds=time.monotonic()-started)
    dump(out/'run_summary.json',summary)
    if args.smoke:
        dump(folder/'preflight_verified.json',summary)
        print('PREFLIGHT_PASSED',json.dumps(dict(thresholds=fixed['thresholds'],elapsed_seconds=summary['elapsed_seconds'])),flush=True)
    else:
        import shutil
        for name in ['complementarios.py','complementarios.sbatch','thresholds_fixed.json','dev_margins.csv','preflight_verified.json']:
            shutil.copy2(folder/name,out/name)
        (out/'README.md').write_text('''# MINION — análisis complementarios

Estos experimentos complementarios reutilizan los artefactos del Trabajo 1; no sustituyen sus resultados principales.
α permanece en 0,85; RRF usa k=60, fijado antes de evaluar. No se ejecutan modelos.

## Experimento 1: combinación convexa frente a RRF

Se toman los rangos originales de top 10 léxico y semántico de los runs TREC. Una ausencia aporta cero.
RRF suma 1/(60+rango), con rangos desde 1; los empates se resuelven por ID ascendente.
Se comprueba igualdad de candidatos por consulta con la combinación convexa guardada.
Se guardan P@3, nDCG@3, métricas por consulta y diferencias RRF menos convexa con IC pareados de 10.000 remuestreos.

## Experimento 2: reranking selectivo

Se invoca el reranker cuando hay al menos cuatro candidatos y el margen fusionado puesto 3 menos puesto 4 es menor o igual al umbral.
Los umbrales se fijaron exclusivamente con los márgenes de las 500 consultas de FiQA-dev durante la prueba previa.
Se usan cuantiles lineales para metas de 25 %, 50 % y 75 %; meta 50 % es la comparación principal.
Los empates en el umbral invocan todos los márgenes iguales: se reportan las tasas reales, sin ajustarlas en test.
Cuando hay menos de cuatro candidatos, se devuelve la fusión; el control aleatorio respeta la misma elegibilidad.

Se simulan las decisiones usando los rankings fused/reranked guardados. Cada control aleatorio tiene exactamente el mismo
número de invocaciones por dataset que su política selectiva y se promedia sobre 100 selecciones sin reemplazo.
Las semillas y las decisiones individuales de cada selección se guardan. Las diferencias contra fusión y el promedio aleatorio
son pareadas por consulta. Sus IC adicionales usan el promedio por consulta de esas 100 selecciones como control fijo;
no son un bootstrap jerárquico de la incertidumbre Monte Carlo.

## Archivos

- `rrf_metrics_*`, `rrf_per_query_*`, `rrf_paired_differences_*`, `rrf_scores_*`: comparación de fusión y sus rangos/puntajes.
- `selective_metrics_*`, `selective_per_query_*`, `selective_paired_differences_*`: relevancia, invocaciones y comparaciones pareadas.
- `selective_decisions_*`: márgenes y decisiones de cada umbral por consulta.
- `random_draw_metrics_*`, `random_decisions_*`, `random_seeds_*`: 100 selecciones, métricas y semillas auditables.
- `thresholds_fixed.json`, `dev_margins.csv`: umbrales de desarrollo congelados y sus márgenes de origen.
- `inputs_manifest.json`, `run_summary.json`, `verification_*`: rutas, huellas, versiones, semillas y validación.
- `experimento_1_fusiones.png`, `experimento_2_selectivo.png`: una figura a 200 dpi por experimento.

La relevancia se calcula con ir_measures y se contrasta con un cálculo explícito de P@3 y nDCG@3 por consulta.
Las entradas de relevancia -1 se conservan y reciben la semántica de sin juicio del evaluador.
Los logs de Slurm están en la carpeta hermana `logs/`. El entorno usado es `.venv` del proyecto del Trabajo 1.

Este análisis evalúa relevancia y número de invocaciones simuladas. No mide latencia ni permite convertir una reducción
de invocaciones en una mejora temporal. Las latencias de estas variantes requieren una prueba aparte.
''')
        dump(out/'outputs_manifest.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='outputs_manifest.json'})
        print('COMPLEMENTARY_ANALYSES_COMPLETE',flush=True)

if __name__=='__main__': main()
