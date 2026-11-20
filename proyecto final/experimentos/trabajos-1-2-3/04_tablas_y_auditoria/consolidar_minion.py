from pathlib import Path
import json,shutil,hashlib,math,tarfile,collections
import numpy as np
import pandas as pd

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'outputs/MINION_integrado'
OUT.mkdir(exist_ok=True)
TABLES=OUT/'04_tablas_y_auditoria'; TABLES.mkdir(exist_ok=True)
SOURCES={
 'fiqa_khipu':BASE/'work/ramas/trabajo2_khipu/paper/minion_trabajo2/results_fiqa_completo_v4',
 'fiqa_kaggle':BASE/'work/ramas/trabajos23_kaggle/paper/khipu/results/fiqa',
 'trec-covid_kaggle':BASE/'work/ramas/trabajos23_kaggle/paper/khipu/results/trec-covid'}
NEW_KHIPU=OUT/'05_trabajo3_khipu_trec'
if (NEW_KHIPU/'results_trec_covid_carga_fija_v4/summary.csv').exists():
    SOURCES['trec-covid_khipu']=NEW_KHIPU/'results_trec_covid_carga_fija_v4'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,default=lambda o: o.item() if isinstance(o,np.generic) else str(o))+'\n',encoding='utf-8')

copies=[(BASE/'outputs/test_results',OUT/'01_trabajo1/relevancia_test'),
 (BASE/'work/ramas/trabajo2_khipu/paper/minion_trabajo2',OUT/'02_trabajo2_khipu_fiqa'),
 (BASE/'work/ramas/trabajos23_kaggle/paper/khipu',OUT/'03_trabajos2y3_kaggle')]
for src,dst in copies:
    shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
dev=OUT/'01_trabajo1/ajuste_dev'; dev.mkdir(parents=True,exist_ok=True)
for name in ['alpha.json','alpha_curve.csv','fiqa_alpha.py','fiqa_alpha.sbatch','slurm-63761.log',
             'slurm_accounting.csv','prepared.json','verification.json','cands_fiqa_dev.parquet']:
    shutil.copy2(BASE/'outputs'/name,dev/name)
comp=OUT/'01_trabajo1/complementarios'; comp.mkdir(exist_ok=True)
with tarfile.open(BASE/'work/complementarios_63778.tar.gz') as tar:
    for member in tar.getmembers():
        resolved=(comp/member.name).resolve()
        assert resolved.is_relative_to(comp.resolve()) and not member.issym() and not member.islnk()
    tar.extractall(comp,filter='data')

CONDS=['L25','L50','L75','L100','NORERANK','NOHEDGE','F1','F2','F3H','F3NH','F4','F5','F6']
ROUTES=['reranked','fused_baseline','fused_fallback','lex','sem','error']
per=[]; aggregates=[]; fitness=[]; pair_checks=[]; inventory=[]; validations=[]; rank_agreement=[]
for series,path in SOURCES.items():
    ds='trec-covid' if series.startswith('trec') else 'fiqa'
    meta=json.loads((path/'run_meta.json').read_text()); cal=json.loads((path/'calibration.json').read_text())
    original=pd.read_csv(path/'summary.csv')
    expected_script=path.parent/'minion_bench.py' if series.endswith('khipu') else path.parents[1]/'minion_bench.py'
    inv=dict(series=series,dataset=ds,environment='Khipu ds001 RTX A6000 compartida' if series.endswith('khipu') else 'Kaggle Tesla T4',
        node=meta.get('node'),job_id=meta.get('slurm_job_id'),capacity_qps=cal['C_qps'] if cal.get('capacity_validated',True) else None,external_load_reference_qps=cal['C_qps'] if cal.get('capacity_validated',True) is False else None,protocol=cal.get('protocol','dataset_capacity_normalized'),hedge_threshold_ms=cal['hedge_threshold_ms'],
        summary_rows=len(original),request_files=len(list(path.glob(f'requests_{ds}_rep*.jsonl'))),
        script_sha256_metadata=meta.get('script_sha256'),script_sha256_present=sha(expected_script),
        script_sha256_LF=hashlib.sha256(expected_script.read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
        script_matches_metadata=meta.get('script_sha256') in [sha(expected_script),hashlib.sha256(expected_script.read_bytes().replace(b'\r\n',b'\n')).hexdigest()],
        corpus_size=meta.get('corpus_size',meta.get('n_docs')),test_queries=meta.get('n_test_queries'),
        metadata_keys=list(meta),calibration_keys=list(cal),gpu=meta.get('gpu'))
    inventory.append(inv)
    if series=='trec-covid_khipu':
        verified=json.loads((NEW_KHIPU/'final_verification.json').read_text())
        inv['corpus_size']=verified['corpus_documents']; inv['test_queries']=verified['test_queries']
        nb=json.loads((NEW_KHIPU/'trabajo3_latencia_trec_covid_khipu.ipynb').read_text())
        cells=[c for c in nb['cells'] if c['cell_type']=='code']
        inv['notebook_code_cells']=len(cells)
        inv['notebook_unexecuted_cells']=sum(c.get('execution_count') is None for c in cells)
        inv['notebook_error_outputs']=sum(o['output_type']=='error' for c in cells for o in c.get('outputs',[]))
    for rep in [1,2,3]:
        loaded={}
        for condition in CONDS:
            file=path/f'requests_{ds}_rep{rep}_{condition}.jsonl'
            raw=[json.loads(line) for line in file.open(encoding='utf-8')]
            loaded[condition]=raw
            records=[r for r in raw if r['t_sched']>=30]
            valid=[r for r in records if r['n_results']==3]
            def pct(v): return 100*sum(v)/len(records) if records else float('nan')
            def pctl(values,q):
                values=sorted(v for v in values if v is not None and np.isfinite(v))
                return values[max(0,math.ceil(q*len(values))-1)] if values else float('nan')
            lat=[r['latency_ms'] for r in valid]
            invoked=sum(r['rerank_invoked'] for r in records); hedged=sum(r['hedge_sent'] for r in records)
            row=dict(series=series,dataset=ds,rep=rep,condition=condition,protocol=inv['protocol'],capacity_qps=inv['capacity_qps'],external_load_reference_qps=inv['external_load_reference_qps'],offered_qps=float(original.loc[(original.rep==rep)&(original.condition==condition),'offered_qps' if 'offered_qps' in original.columns else 'qps_offered'].iloc[0]),n_sent=len(records),n_valid=len(valid),
                p50_ms=pctl(lat,.5),p95_ms=pctl(lat,.95),p99_ms=pctl(lat,.99),
                rerank_p99_ms=pctl([r.get('stage_ms',{}).get('rerank') for r in valid if r['route']=='reranked' and r['rerank_invoked']],.99),
                continuity_pct=pct(r['n_results']==3 and r['latency_ms']<=2500 for r in records),
                errors_pct=pct(r['route']=='error' for r in records),
                dup_pct=100*hedged/invoked if invoked else float('nan'),invoked=invoked,hedged=hedged)
            for route in ROUTES: row['route_'+route]=pct(r['route']==route for r in records)
            per.append(row)
            orig=original[(original.rep==rep)&(original.condition==condition)].iloc[0]
            checks={}
            for col in ['p50_ms','p95_ms','p99_ms','continuity_pct']:
                a,b=row[col],orig[col]
                checks[col]=bool((pd.isna(a) and pd.isna(b)) or np.isclose(a,b,atol=.0011,rtol=0))
            col='pct_dup' if 'pct_dup' in orig.index else 'dup_pct'
            a,b=row['dup_pct'],orig[col]
            checks['dup_pct']=bool((pd.isna(a) and pd.isna(b)) or (invoked==0 and b==0) or np.isclose(a,b,atol=.0011,rtol=0))
            validations.append(dict(series=series,rep=rep,condition=condition,**checks))
        a,b=loaded['F3H'],loaded['F3NH']
        pair_checks.append(dict(series=series,rep=rep,requests_H=len(a),requests_NH=len(b),
            qids_equal=[r['qid'] for r in a]==[r['qid'] for r in b],
            schedules_equal=[r['t_sched'] for r in a]==[r['t_sched'] for r in b],
            injected_delays_equal=[r.get('delay_injected') for r in a]==[r.get('delay_injected') for r in b],observed_delay_mismatches=sum(x.get('delay_injected')!=y.get('delay_injected') for x,y in zip(a,b))))
    # Notebook files exist only in Kaggle branch; verify actual execution.
    if series.endswith('kaggle'):
        file=path.parents[1]/('trabajo2_latencia_fiqa.ipynb' if ds=='fiqa' else 'trabajo3_latencia_trec-covid.ipynb')
        nb=json.loads(file.read_text(encoding='utf-8'))
        cells=[c for c in nb['cells'] if c['cell_type']=='code']
        inv['notebook_code_cells']=len(cells)
        inv['notebook_unexecuted_cells']=sum(c.get('execution_count') is None for c in cells)
        inv['notebook_error_outputs']=sum(o['output_type']=='error' for c in cells for o in c.get('outputs',[]))

frame=pd.DataFrame(per); frame.to_csv(TABLES/'latencia_por_repeticion.csv',index=False)
for (series,condition),g in frame.groupby(['series','condition'],sort=False):
    row=dict(series=series,condition=condition,protocol=g.protocol.iloc[0],capacity_qps=g.capacity_qps.iloc[0],external_load_reference_qps=g.external_load_reference_qps.iloc[0],offered_qps=g.offered_qps.iloc[0],repetitions=len(g),n_requests=int(g.n_sent.sum()))
    for col in ['p50_ms','p95_ms','p99_ms','rerank_p99_ms','continuity_pct','dup_pct']:
        row[col+'_median']=g[col].median(); row[col+'_min']=g[col].min(); row[col+'_max']=g[col].max()
    for route in ROUTES: row['route_'+route+'_mean']=g['route_'+route].mean()
    aggregates.append(row)
for (series,rep),g in frame.groupby(['series','rep']):
    load=g[g.condition.isin(['L25','L50','L75','L100'])]
    fault=g[g.condition.isin(['F1','F2'])]
    dup=g[g.condition.isin(['L25','L50','L75','L100','F3H'])]
    fitness.append(dict(series=series,rep=rep,protocol=g.protocol.iloc[0],worst_load_p99_ms=load.p99_ms.max(),fitness_i=load.p99_ms.max()<=2500,
        worst_F1F2_continuity_pct=fault.continuity_pct.min(),fitness_iii=fault.continuity_pct.min()>=99,
        worst_duplicates_pct=dup.dup_pct.max(),fitness_iv=dup.dup_pct.max()<=10))
pd.DataFrame(aggregates).to_csv(TABLES/'latencia_mediana_y_rango.csv',index=False)
pd.DataFrame(fitness).to_csv(TABLES/'fitness_por_repeticion.csv',index=False)
pd.DataFrame(pair_checks).to_csv(TABLES/'pareamiento_hedging.csv',index=False)
pd.DataFrame(validations).to_csv(TABLES/'verificacion_summaries.csv',index=False)
dump(TABLES/'inventario_series.json',inventory)
branches=dict(main='f749842d94371a198228799af29b763d621364b4',
    **{'paper/trabajo2':'650c992c4dd6aabd73b06ed9a218eb763ce80fba','feat/khipu-kaggle-results':'45e4db4e0cdf7c82375b6e1596a168737a07ac38'})
dump(OUT/'procedencia.json',dict(repository='https://github.com/Fabryzzio-Meza-Torres/arquitectura-de-software',
    branches=branches,work1_jobs=[63761,63769],complementary_job=63778,work3_capacity_attempt_job=63911,work3_fixed_load_job=63919,work3_analysis_job=63913,
    work3_khipu_job=json.loads((NEW_KHIPU/'results_trec_covid_carga_fija_v4/run_meta.json').read_text())['slurm_job_id'] if NEW_KHIPU.exists() else None,
    preserved_sources=True,original_branches_modified=False))
print('INVENTORY',json.dumps(inventory,ensure_ascii=False))
print('VALIDATION',pd.DataFrame(validations).select_dtypes('bool').all().to_dict())
print('FITNESS',pd.DataFrame(fitness).to_string(index=False))
print('PAIRS',pd.DataFrame(pair_checks).to_string(index=False))
important=pd.DataFrame(aggregates)
print('LATENCY',important[important.condition.isin(['L100','NORERANK','F1','F2','F3H','F3NH','F4','F5','F6'])][[
    'series','condition','n_requests','p99_ms_median','p99_ms_min','p99_ms_max','continuity_pct_min','dup_pct_max','route_reranked_mean','route_fused_fallback_mean']].to_string(index=False))
