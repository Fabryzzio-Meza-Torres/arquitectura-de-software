#!/usr/bin/env python3
"""Check that quality run wrote one consistent record per query and no duplicate candidates."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('--expected',type=int,default=None);a=p.parse_args()
rows=[json.loads(x) for x in Path(a.file).read_text(encoding='utf8').splitlines() if x.strip()]
ids=[r['query_id'] for r in rows]
assert len(ids)==len(set(ids)), 'Consultas duplicadas en checkpoint'
for r in rows:
    dids=[x['doc_id'] for x in r['candidates']]
    assert len(dids)==len(set(dids)),f"Candidatos repetidos en {r['query_id']}"
    assert set(r['ranking_A'])==set(dids)==set(r['ranking_B'])
    assert r['ranking_A'][:5]==r['top5_A']
    assert r['ranking_B'][:5]==r['top5_B']
if a.expected is not None:assert len(rows)==a.expected,(len(rows),a.expected)
print('OK, consultas únicas:',len(rows),'sin duplicados; rankings consistentes')
