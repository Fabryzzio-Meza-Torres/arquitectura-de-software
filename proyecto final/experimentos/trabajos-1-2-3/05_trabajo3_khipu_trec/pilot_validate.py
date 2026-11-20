from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
assert hashlib.sha256((root/'minion_bench.py').read_bytes()).hexdigest()=='bb027763a577074373d5c1909467fbac67f8b5484d37696b29e1f697f02f22b7'
meta=json.loads((root/'pilot/run_meta.json').read_text())
assert meta['node']=='ds001' and 'RTX A6000' in meta['nvidia_smi']
assert meta['alpha_json']['alpha']==.85
assert meta['args']['subset']==2000 and meta['args']['fake'] is False
checks={}
for condition,expected in [('L100','reranked'),('F1','fused_fallback'),('F2','fused_fallback'),
    ('F3H','reranked'),('F3NH','reranked'),('F4','lex'),('F5','sem'),('F6','error')]:
    path=root/'pilot'/f'requests_trec-covid_rep1_{condition}.jsonl'
    rows=[json.loads(line) for line in path.open()]
    selected=[r for r in rows if r['t_sched']>=5]
    assert selected and sum(r['route']==expected for r in selected)/len(selected)>=.95,condition
    assert all(r['n_results']==(0 if condition=='F6' else 3) for r in selected),condition
    checks[condition]={'n':len(selected),'expected_route':expected}
a=[json.loads(x) for x in (root/'pilot/requests_trec-covid_rep1_F3H.jsonl').open()]
b=[json.loads(x) for x in (root/'pilot/requests_trec-covid_rep1_F3NH.jsonl').open()]
assert [(x['qid'],x['t_sched'],x['delay_injected']) for x in a]==[(x['qid'],x['t_sched'],x['delay_injected']) for x in b]
result=dict(passed=True,pilot=True,subset=2000,checks=checks,paired_fault_injection_verified=True)
(root/'pilot/verification.json').write_text(json.dumps(result,indent=2))
print('PILOT_PASSED',json.dumps(result),flush=True)
