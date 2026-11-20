#!/usr/bin/env python3
"""MINION phase 1 only: full FiQA corpus, dev qrels, cached hybrid alpha tuning.

Run prepare on the login node (downloads only); run pilot/full through Slurm.
Document ties: ascending UTF-8 document ID, including top-10 boundaries.
BGE: fp16 forward, CLS pooling, L2 normalize in float32, exact FlatIP retrieval.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import socket
import time

PREFIX = 'Represent this sentence for searching relevant passages: '
MODEL = 'BAAI/bge-base-en-v1.5'


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def prepare(root):
    import urllib.request
    import zipfile
    from huggingface_hub import HfApi, snapshot_download
    data = root / 'data'
    data.mkdir(exist_ok=True)
    archive = data / 'fiqa.zip'
    if not archive.exists():
        urllib.request.urlretrieve('https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/fiqa.zip', archive)
    with zipfile.ZipFile(archive) as z:
        # No test/train qrels are extracted or read.
        for name in ['fiqa/corpus.jsonl', 'fiqa/queries.jsonl', 'fiqa/qrels/dev.tsv']:
            z.extract(name, data)
    revision = HfApi().model_info(MODEL).sha
    snapshot_download(MODEL, revision=revision, local_dir=root / 'models' / 'bge',
                      allow_patterns=['config.json', 'model.safetensors', 'tokenizer.json',
                                      'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt'])
    dump(root / 'prepared.json', {'model': MODEL, 'revision': revision,
         'archive_sha256': sha(archive), 'files': {p: sha(data / 'fiqa' / p)
         for p in ['corpus.jsonl', 'queries.jsonl', 'qrels/dev.tsv']}})
    print('PREPARED', flush=True)


def execute(root, pilot):
    start = time.monotonic()
    import importlib.metadata as md
    import numpy as np
    import pandas as pd
    import torch
    import bm25s
    import Stemmer
    import faiss
    import ir_measures as irm
    from transformers import AutoTokenizer, AutoModel

    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(int(os.environ.get('SLURM_CPUS_PER_TASK', '4')))
    faiss.omp_set_num_threads(torch.get_num_threads())
    assert torch.cuda.is_available(), 'GPU is required for fp16 encoding'
    out = root / ('pilot' if pilot else 'results')
    out.mkdir(exist_ok=True)
    cache = root / 'cache'
    cache.mkdir(exist_ok=True)
    summary = {'mode': 'pilot' if pilot else 'full', 'node': socket.gethostname(),
               'job_id': os.environ.get('SLURM_JOB_ID'), 'gpu': torch.cuda.get_device_name(0),
               'versions': {p: md.version(p) for p in ['torch', 'transformers', 'numpy',
                   'bm25s', 'PyStemmer', 'faiss-cpu', 'ir_measures', 'pandas', 'pyarrow']},
               'prepared': json.loads((root / 'prepared.json').read_text()),
               'scope': 'FiQA full corpus and dev only; no reranker, test or TREC-COVID'}

    def checkpoint(stage):
        summary.update(stage=stage, elapsed_seconds=time.monotonic() - start)
        dump(out / 'run_summary.json', summary)
        print(stage, summary['elapsed_seconds'], flush=True)

    data = root / 'data' / 'fiqa'
    qr = pd.read_csv(data / 'qrels/dev.tsv', sep='\t', dtype={'query-id': str, 'corpus-id': str})
    qr = qr.rename(columns={'query-id': 'query_id', 'corpus-id': 'doc_id', 'score': 'relevance'})
    qids = sorted(set(qr.query_id))
    queries = {}
    for line in (data / 'queries.jsonl').open():
        row = json.loads(line)
        if row['_id'] in qids:
            queries[row['_id']] = row['text']
    docs = [json.loads(line) for line in (data / 'corpus.jsonl').open()]
    docs.sort(key=lambda d: d['_id'])
    ids = np.array([d['_id'] for d in docs])
    assert len(docs) == 57638 and len(set(ids)) == 57638
    assert len(qids) == len(queries) == 500 and not qr.duplicated(['query_id', 'doc_id']).any()
    assert set(qr.doc_id).issubset(set(ids))
    assert set(qr.query_id) == set(queries)
    assert (qr.groupby('query_id').relevance.max() >= 1).all()
    dump(out / 'counts.json', {'corpus': len(docs), 'dev_queries': len(qids), 'dev_qrels': len(qr)})
    if pilot:
        qids = qids[:5]
    qr = qr[qr.query_id.isin(qids)].copy()
    texts = [d['title'] + ' ' + d['text'] for d in docs]
    checkpoint('data_validated')

    stemmer = Stemmer.Stemmer('english')
    index_path = cache / 'bm25'
    if index_path.exists():
        bm = bm25s.BM25.load(str(index_path), load_corpus=False)
    else:
        bm = bm25s.BM25(k1=0.9, b=0.4, method='lucene')
        bm.index(bm25s.tokenize(texts, stopwords='en', stemmer=stemmer))
        bm.save(str(index_path))
    checkpoint('bm25_ready')

    tokenizer = AutoTokenizer.from_pretrained(root / 'models/bge', local_files_only=True)
    model = AutoModel.from_pretrained(root / 'models/bge', local_files_only=True,
                                     torch_dtype=torch.float16, attn_implementation='eager').cuda().eval()

    def encode(strings, target, batch=32):
        if target.exists():
            emb = np.load(target)
            assert emb.shape == (len(strings), 768) and emb.dtype == np.float32
            return emb
        chunks = []
        for i in range(0, len(strings), batch):
            inputs = tokenizer(strings[i:i+batch], padding=True, truncation=True,
                               max_length=512, return_tensors='pt').to('cuda')
            with torch.inference_mode():
                v = model(**inputs).last_hidden_state[:, 0].float()
                v = torch.nn.functional.normalize(v, p=2, dim=1)
            chunks.append(v.cpu().numpy())
            if i % 3200 == 0:
                print('encode', target.name, i, '/', len(strings), flush=True)
        emb = np.ascontiguousarray(np.concatenate(chunks), dtype=np.float32)
        assert np.isfinite(emb).all() and np.allclose(np.linalg.norm(emb, axis=1), 1, atol=1e-5)
        tmp = target.with_suffix('.tmp.npy')
        np.save(tmp, emb)
        tmp.replace(target)
        return emb

    # Pilot uses 256 real documents; full job is not submitted until pilot passes.
    n = 256 if pilot else len(docs)
    corpus_emb = encode(texts[:n], cache / ('pilot_emb.npy' if pilot else 'emb_fiqa.npy'))
    query_emb = encode([PREFIX + queries[q] for q in qids], cache / ('pilot_queries.npy' if pilot else 'emb_dev.npy'))
    dense = faiss.IndexFlatIP(768)
    dense.add(corpus_emb)
    checkpoint('embeddings_ready')

    def norm(x):
        return np.ones_like(x) if x.max() == x.min() else (x-x.min())/(x.max()-x.min())

    assert np.array_equal(norm(np.array([2., 2.])), np.ones(2))
    rows = []
    for qi, qid in enumerate(qids):
        tokens = bm25s.tokenize([queries[qid]], stopwords='en', stemmer=stemmer, return_ids=False)[0]
        lex = np.asarray(bm.get_scores(tokens))
        assert lex.shape == (len(docs),)
        # Corpus IDs sorted ascending; stable sort resolves equal lexical scores.
        lt = np.argsort(-lex, kind='stable')[:10]
        # Search all exact IP scores so equal-score ties at rank 10 are also resolved by ID.
        distances, positions = dense.search(query_emb[qi:qi+1], n)
        sem_all = np.empty(n, dtype=np.float32)
        sem_all[positions[0]] = distances[0]
        st = np.argsort(-sem_all, kind='stable')[:10]
        cand = sorted(set(lt.tolist()) | set(st.tolist()))
        lr = lex[cand].astype(np.float64)
        # Explicit stored-embedding dot product for BOTH routes' candidates.
        # Pilot's lex-only candidates may lie outside its small dense index.
        missing = [i for i in cand if i >= n]
        extra = encode([texts[i] for i in missing], cache / f'pilot_extra_{qid}.npy') if missing else None
        extra_map = dict(zip(missing, extra)) if missing else {}
        sr = np.array([np.dot(corpus_emb[i] if i < n else extra_map[i], query_emb[qi]) for i in cand], dtype=np.float64)
        assert len(cand) <= 20 and len(cand) >= 10
        ln, sn = norm(lr), norm(sr)
        assert np.isfinite(lr).all() and np.isfinite(sr).all()
        for j, di in enumerate(cand):
            rows.append({'query_id': qid, 'doc_id': ids[di], 'lex_raw': lr[j], 'sem_raw': sr[j],
                         'lex_norm': ln[j], 'sem_norm': sn[j], 'in_lex': di in lt, 'in_sem': di in st})
    candidates = pd.DataFrame(rows)
    assert not candidates.duplicated(['query_id', 'doc_id']).any()
    candidates.to_parquet(out / 'cands_fiqa_dev.parquet', index=False)
    checkpoint('candidate_scores_saved')

    measures = [irm.P(rel=1)@3, irm.nDCG@3]
    curve = []
    groups = list(candidates.groupby('query_id', sort=True))
    for step in range(21):
        alpha = step / 20
        runrows = []
        ps, ns = [], []
        for qid, g in groups:
            g = g.assign(fused=(1-alpha)*g.lex_norm + alpha*g.sem_norm)
            g = g.sort_values(['fused', 'doc_id'], ascending=[False, True], kind='stable')
            # Rank-derived unique scores force the chosen deterministic tie order in ir_measures.
            runrows += [{'query_id': qid, 'doc_id': d, 'score': float(len(g)-r)}
                        for r, d in enumerate(g.doc_id)]
            relevance = dict(zip(qr[qr.query_id == qid].doc_id, qr[qr.query_id == qid].relevance))
            grades = [relevance.get(d, 0) for d in g.doc_id[:3]]
            ps.append(sum(r >= 1 for r in grades)/3)
            ideal = sorted(relevance.values(), reverse=True)[:3]
            dcg = sum(r/np.log2(k+2) for k, r in enumerate(grades))
            idcg = sum(r/np.log2(k+2) for k, r in enumerate(ideal))
            ns.append(dcg/idcg if idcg else 0.)
        values = irm.calc_aggregate(measures, qr, pd.DataFrame(runrows))
        p, ndcg = float(values[measures[0]]), float(values[measures[1]])
        assert np.isclose(p, np.mean(ps), atol=1e-12)
        assert np.isclose(ndcg, np.mean(ns), atol=1e-12)
        curve.append({'alpha': alpha, 'precision_at_3': p, 'ndcg_at_3': ndcg})
    curve_df = pd.DataFrame(curve)
    curve_df.to_csv(out / 'alpha_curve.csv', index=False, float_format='%.17g')
    best = sorted(curve, key=lambda r: (-r['precision_at_3'], -r['ndcg_at_3'], r['alpha']))[0]
    result = dict(best, selection_rule='max P@3; then max nDCG@3; then min alpha',
                  dataset='FiQA', split='dev', n_queries=len(qids), n_documents=len(docs),
                  seed=42, fusion='(1-alpha)*lex_norm + alpha*sem_norm',
                  normalization='per-query candidate min-max; constant scores -> 1.0',
                  document_tie_break='ascending document ID (string)',
                  model=MODEL, model_revision=summary['prepared']['revision'],
                  encoding='fp16 forward; CLS pooling; L2 float32; stored float32',
                  bm25={'library': 'bm25s', 'method': 'lucene', 'k1': 0.9, 'b': 0.4,
                        'stopwords': 'en', 'stemmer': 'english (PyStemmer)', 'top_k': 10},
                  semantic={'query_prefix': PREFIX, 'max_length': 512, 'normalize': True,
                            'index': 'faiss.IndexFlatIP', 'top_k': 10},
                  candidate_sha256=sha(out / 'cands_fiqa_dev.parquet'),
                  script_sha256=sha(Path(__file__)), pilot=pilot,
                  node=summary['node'], slurm_job_id=summary['job_id'])
    dump(out / 'alpha.json', result)
    check = pd.read_csv(out / 'alpha_curve.csv')
    winner = check.sort_values(['precision_at_3', 'ndcg_at_3', 'alpha'], ascending=[False, False, True]).iloc[0]
    assert len(check) == 21 and check.alpha.nunique() == 21
    assert np.allclose(check.alpha, np.arange(21)/20)
    assert winner.alpha == result['alpha']
    summary['best'] = best
    summary['candidate_rows'] = len(candidates)
    checkpoint('PILOT_PASSED' if pilot else 'COMPLETE_VERIFIED')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--pilot', action='store_true')
    args = parser.parse_args()
    prepare(args.root) if args.prepare else execute(args.root, args.pilot)
