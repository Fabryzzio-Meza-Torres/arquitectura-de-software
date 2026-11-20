#!/usr/bin/env python3
"""One frozen 10k random sample of the original FiQA corpus, retaining original queries/qrels.
Do NOT preferentially include positives: matches the shared TREC protocol.
"""
import json,random,shutil,hashlib,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);args=p.parse_args()
src=Path(args.source);out=Path(args.out)
if not (src/'corpus.jsonl').exists():raise FileNotFoundError(f'Missing BEIR source: {src}/corpus.jsonl')
if src.resolve()==out.resolve():raise ValueError('output must differ from source')
if (out/'corpus.jsonl').exists():raise FileExistsError('Output corpus already exists; do not overwrite a frozen sample')
out.mkdir(parents=True,exist_ok=True)
with open(src/'corpus.jsonl',encoding='utf8') as f: docs=[json.loads(x) for x in f]
assert len(docs)>=10000
ids=[str(x['_id']) for x in docs];assert len(set(ids))==len(ids)
chosen=set(random.Random(42).sample(ids,10000))
selected=[x for x in docs if str(x['_id']) in chosen]
with open(out/'corpus.jsonl','w',encoding='utf8') as f:
    for doc in selected:f.write(json.dumps(doc,ensure_ascii=False)+'\n')
shutil.copy2(src/'queries.jsonl',out/'queries.jsonl')
shutil.copytree(src/'qrels',out/'qrels',dirs_exist_ok=True)
sha=hashlib.sha256((out/'corpus.jsonl').read_bytes()).hexdigest()
with open(out/'manifest.json','w') as f:json.dump({'dataset':'fiqa','seed':42,'original_docs':len(docs),'selected_docs':len(selected),'sha256':sha},f,indent=2)
print('OK original:',len(docs),'selected:',len(selected),'sha256:',sha)
