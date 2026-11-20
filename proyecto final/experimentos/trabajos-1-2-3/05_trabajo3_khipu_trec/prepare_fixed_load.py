"""Explicit load adapter: FiQA's 8 QPS is NOT a validated TREC capacity."""
from pathlib import Path
import json, hashlib, re, sys
import minion_bench as bench

root=Path(__file__).resolve().parent
attempt=root/'results_trec_covid_completo_v4'
out=root/'results_trec_covid_carga_fija_v4'
records=[json.loads(s) for s in (attempt/'requests_trec-covid_calib_1qps.jsonl').read_text().splitlines()]
reference=json.loads((root/'reference_fiqa_run_meta.json').read_text())
assert len(records)==500 and reference['calibration_json']['C_qps']==8
ok=[r for r in records if r['route']=='reranked']
stages={s:{f'p{q}':bench.pctl([r['stage_ms'][s] for r in ok],q) for q in [50,95,99]} for s in bench.STAGES}
for s in stages: stages[s]['n']=len(ok)
log=(root/'logs/trec-completo-v4-63911.log').read_text(errors='replace')
pattern=r'([\d.]+) QPS: logrado ([\d.]+) \| p99 ([\d.]+)->([\d.]+) ms \| reranked ([\d.]+)% \| ruta completa (OK|NO) \| cualquier ruta (OK|NO)'
ramp=[dict(offered_qps=float(a),achieved_qps_rounded=float(b),p99_first_half_ms_rounded=float(c),p99_second_half_ms_rounded=float(d),reranked_pct_rounded=float(e),passes=f=='OK',passes_any=g=='OK') for a,b,c,d,e,f,g in re.findall(pattern,log)]
plan=dict(protocol='complementary_fixed_absolute_load',capacity_validated=False,trec_capacity_qps=None,
 C_qps=8,C_role='EXTERNAL LOAD SCALE ONLY; NOT TREC CAPACITY',reference_fiqa_job='63828',
 reference_fiqa_capacity_qps=8,failed_capacity_job='63911',hedge_threshold_ms=stages['rerank']['p95'],
 stage_percentiles_1qps_ms=stages,n_calib_queries=500,ramp_log_rounded=ramp,
 fixed_loads_qps={'L25':2,'L50':4,'L75':6,'L100':8,'NORERANK':8,'NOHEDGE':8,'F1_F6':6},
 note='Exact v4 benchmark in --phase runs. C_qps is only an adapter for fixed loads selected from the pre-existing FiQA reference. TREC failed the unmodified v4 capacity criterion. Do not report 8 QPS as TREC capacity.',
 source_calibration_sha256=hashlib.sha256((attempt/'requests_trec-covid_calib_1qps.jsonl').read_bytes()).hexdigest())
if '--dry-run' in sys.argv:
 print(json.dumps(dict(validated_inputs=True,n=len(records),reranked=len(ok),threshold_ms=plan['hedge_threshold_ms'],ramp_steps_so_far=len(ramp),protocol=plan['protocol'])))
else:
 assert 'no se puede fijar C con este criterio' in log and len(ramp)==7
 assert ramp[0]['passes'] is False
 assert not (attempt/'calibration.json').exists(), 'Do not replace a successful calibration'
 out.mkdir(exist_ok=True)
 assert not (out/'summary.csv').exists(), 'Do not overwrite a measured run'
 text=json.dumps(plan,indent=2,ensure_ascii=False)+'\n'
 (out/'calibration.json').write_text(text)
 (root/'fixed_load_plan.json').write_text(text)
 print(json.dumps(dict(prepared=True,protocol=plan['protocol'],threshold_ms=plan['hedge_threshold_ms'],trec_capacity_qps=None)))
