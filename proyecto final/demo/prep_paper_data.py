from pathlib import Path
import json,csv,math
import argparse
parser=argparse.ArgumentParser(description='Export saved MINION rankings for the desktop demo')
parser.add_argument('--trec',type=Path,required=True)
parser.add_argument('--fiqa',type=Path,required=True)
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'app/public/paperdata')
args=parser.parse_args()
T,F,B,OUT=args.trec,args.fiqa,args.baseline,args.output
OUT.mkdir(parents=True,exist_ok=True)
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def metric(ids,rel):
 r=[max(0,rel.get(d,0)) for d in ids];ideal=sorted([max(0,v) for v in rel.values()],reverse=True)
 dcg=lambda a:sum((2**g-1)/math.log2(i+2) for i,g in enumerate(a[:3]))
 return dict(P3=sum(v>0 for v in r[:3])/3,nDCG3=dcg(r)/dcg(ideal) if dcg(ideal) else 0,MRR10=next((1/(i+1) for i,v in enumerate(r[:10]) if v>0),0))
manifest={}
for ds in ['trec','fiqa']:
 corpus=T/'entrada_comun/corpus_10000.jsonl' if ds=='trec' else F/'data/fiqa/corpus.jsonl'
 docs={str(r['_id']):r for r in map(json.loads,corpus.read_text(encoding='utf-8').splitlines())}
 if ds=='trec':
  queries=json.loads((T/'resultados/consultas.json').read_text(encoding='utf-8'));rel=json.loads((T/'resultados/qrels.json').read_text(encoding='utf-8'))
  cand=json.loads((T/'resultados/candidatos.json').read_text(encoding='utf-8'));rr=json.loads((T/'resultados/rankings.json').read_text(encoding='utf-8'))
  llm={(r['qid'],r['docid']):r['score'] for r in json.loads((T/'resultados/scores_llm.json').read_text(encoding='utf-8'))}
  records=[dict(id=q,query=queries[q],rankA=rr[q]['fusion'],rankB=rr[q]['LLM'],cands=[dict(id=x['id'],lex=x['lex'],sem=x['sem'],fus=x['fused'],llm=llm[q,x['id']]) for x in xs]) for q,xs in cand.items()]
 else:
  rel={}
  with (F/'data/fiqa/qrels/test.tsv').open(encoding='utf-8') as f:
   for r in csv.DictReader(f,delimiter='\t'):
    if r['corpus-id'] in docs:rel.setdefault(r['query-id'],{})[r['corpus-id']]=int(r['score'])
  records=[]
  for r in map(json.loads,(F/'results/calidad/candidates_scores.jsonl').read_text(encoding='utf-8').splitlines()):
   records.append(dict(id=r['query_id'],query=r['query'],rankA=r['ranking_A'],rankB=r['ranking_B'],cands=[dict(id=x['doc_id'],lex=x['lex_score'],sem=x['sem_score'],fus=x['fusion'],llm=x['llm_score']) for x in r['candidates']]))
 baseline=json.loads((B/ds/'resultados/rankings.json').read_text(encoding='utf-8'))
 idx=[]
 for r in records:
  q=r['id'];labels=rel.get(q,{});r['rankS']=baseline[q]['semantic']
  by={c['id']:c for c in r['cands']}
  for docid in sorted(set(r['rankS'])|set(r['rankA'])|set(r['rankB'])):
   if docid not in by:by[docid]=dict(id=docid,lex=None,sem=None,fus=None,llm=None)
  original_ids=[c['id'] for c in r['cands']]
  for c in by.values():
   doc=docs[c['id']];c.update(title=doc.get('title') or ('Documento '+c['id']),text=doc.get('text','')[:2400],rel=labels.get(c['id']),lexNorm=None,semNorm=None)
  for key,target in [('lex','lexNorm'),('sem','semNorm')]:
   values=[by[d][key] for d in original_ids];lo=min(values);hi=max(values)
   for d in original_ids:by[d][target]=(by[d][key]-lo)/(hi-lo) if hi>lo else 1
  r['cands']=list(by.values());r['metrics']={m:metric(r[k],labels) for m,k in [('semantic','rankS'),('fusion','rankA'),('llm','rankB')]}
  r['poolSize']=len(original_ids)
  row=dict(id=q,query=r['query'],hit=any(v>0 for v in labels.values()),gain=r['metrics']['fusion']['P3']-r['metrics']['semantic']['P3'],llmGain=r['metrics']['llm']['P3']-r['metrics']['fusion']['P3'])
  idx.append(row);write(OUT/ds/'q'/f'{q}.json',r)
 with (B/ds/'resultados/metricas_resumen.csv').open() as f:quality={r['method']:r for r in csv.DictReader(f)}
 with (B/ds/'resultados/latencia_resumen.csv').open() as f:latency={r['method']:r for r in csv.DictReader(f)}
 ci=list(csv.DictReader((B/ds/'resultados/diferencias_pareadas.csv').open()))
 manifest[ds]=dict(queries=len(idx),documents=10000,quality=quality,latency=latency,ci=ci,
  hardware='A100 MIG 20 GB · ag001' if ds=='trec' else 'RTX A6000 · ds001',
  originalLLMMedianMs=7230.908 if ds=='trec' else 930.264,
  llmLatencyN=1000 if ds=='trec' else 50,
  source='TREC/Qwen: aebd118; FiQA/Qwen: 5926a7e; baseline: jobs64172/64173',index=idx)
write(OUT/'manifest.json',manifest)
print({d:len(x['index']) for d,x in manifest.items()})
