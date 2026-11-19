import json, csv, os, statistics, glob
import pathlib; R=str(pathlib.Path(__file__).resolve().parents[1]/'minion_fiqa_llm_v2')
OUT=str(pathlib.Path(__file__).resolve().parent/'app/public/data'); os.makedirs(OUT+'/q',exist_ok=True)
docs={}
for l in open(R+'/data/fiqa/corpus.jsonl'):
    d=json.loads(l); docs[str(d['_id'])]=((d.get('title') or '')+' '+(d.get('text') or '')).strip()
qrels={}
for r in csv.DictReader(open(R+'/data/fiqa/qrels/test.tsv'),delimiter='\t'):
    qrels.setdefault(r['query-id'],{})[r['corpus-id']]=int(float(r['score']))
met={}
for r in csv.DictReader(open(R+'/results/calidad/metrics_per_query.csv')):
    met.setdefault(r['query_id'],{})[r['arm']]={k:float(r[k]) for k in ['p@3','ndcg@3','mrr@10']}
index=[]
for l in open(R+'/results/calidad/candidates_scores.jsonl'):
    r=json.loads(l); qid=r['query_id']; rel=qrels.get(qid,{})
    c=[dict(id=x['doc_id'],text=docs[x['doc_id']][:420],rel=rel.get(x['doc_id'],0),
        lex=round(x['lex_norm'],4),sem=round(x['sem_norm'],4),fus=round(x['fusion'],4),llm=round(x['llm_score'],4)) for x in r['candidates']]
    hit=any(x['rel']>0 for x in c)
    json.dump(dict(id=qid,query=r['query'],cands=c,rankA=r['ranking_A'],rankB=r['ranking_B'],times=r['times']),open(f'{OUT}/q/{qid}.json','w'),ensure_ascii=False)
    m=met.get(qid,{})
    index.append(dict(id=qid,query=r['query'],hit=hit,A=m.get('A'),B=m.get('B'),t=r['times']))
json.dump(index,open(OUT+'/index.json','w'),ensure_ascii=False)
def j(p): return json.load(open(R+'/results/'+p))
lat={a:[json.loads(l) for l in open(R+f'/results/latencia/latency_{a}_c1_requests.jsonl')] for a in 'AB'}
bt={}
for l in open(R+'/results/batching/batch_runs.jsonl'):
    x=json.loads(l); bt.setdefault(x['batch'],[]).append(x['seconds'])
summary=dict(quality=j('calidad/summary.json'),
  latency={a:j(f'latencia/latency_{a}_c1_summary.json') for a in 'AB'},
  concurrency=[j(f'concurrencia/concurrency_B_c{c}_summary.json') for c in (1,2,4)],
  batching={str(b):dict(mean_s=statistics.mean(v),n=len(v)) for b,v in sorted(bt.items())},
  latSamples={a:[round(x['total_ms'],1) for x in lat[a]] for a in 'AB'},
  llmMs=[round(x['llm_ms'],1) for x in lat['B']], searchMs=[round(x['search_ms'],1) for x in lat['B']])
json.dump(summary,open(OUT+'/summary.json','w'))
print(len(index),sum(i['hit'] for i in index),summary['batching'])
