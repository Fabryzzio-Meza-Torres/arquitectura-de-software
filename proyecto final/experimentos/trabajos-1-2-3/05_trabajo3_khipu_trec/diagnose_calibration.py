from pathlib import Path
import json,collections,math
root=Path(__file__).resolve().parent
path=root/'results_trec_covid_completo_v4/requests_trec-covid_calib_1qps.jsonl'
rows=[json.loads(line) for line in path.open()]
routes=collections.Counter(r['route'] for r in rows)
timeouts=collections.Counter(s for r in rows for s in r['timeouts'])
errors=collections.Counter(s for r in rows for s in r['errors'])
bad=[r for r in rows if r['route']!='reranked']
print(json.dumps(dict(n=len(rows),routes=dict(routes),timeouts=dict(timeouts),errors=dict(errors),
    non_reranked=[{k:r.get(k) for k in ['qid','route','timeouts','errors','latency_ms','stage_ms']} for r in bad]),indent=2))
