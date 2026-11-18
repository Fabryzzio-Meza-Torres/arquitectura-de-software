#!/usr/bin/env python
"""MINION latency and failure benchmark (Trabajos 2 y 3).

Single-process asyncio service: parallel BM25 + dense retrieval, convex fusion,
cross-encoder reranking with hedged requests, fault injection and an open-loop
Poisson load generator. Spec: TRABAJO_2y3_latencia_khipu.md (sections 2-5).
"""
import argparse
import asyncio
import csv
import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

CONFIG = {
    "seed": 42,
    "datasets": {
        "fiqa": "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/fiqa.zip",
        "trec-covid": "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/trec-covid.zip",
    },
    "doc_text": "title + ' ' + text",
    "lexical": {"lib": "bm25s", "method": "lucene", "k1": 0.9, "b": 0.4, "stopwords": "en",
                "stemmer": "english (PyStemmer)", "top_k": 10},
    "semantic": {"model": "BAAI/bge-base-en-v1.5", "model_revision": "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
                 "query_prefix": "Represent this sentence for searching relevant passages: ",
                 "encoding": "forward en fp16; pooling CLS; normalización L2; se guarda en float32",
                 "index": "faiss.IndexFlatIP", "max_length": 512, "top_k": 10},
    "fusion": {"normalization": "min-max por consulta; si max == min -> 1.0",
               "formula": "(1 - alpha) * lex_norm + alpha * sem_norm",
               "alpha": "leer de alpha.json (= 0.85)",
               "tie_break": "ID del documento ascendente (como string), también en el corte del top 10"},
    "reranker": {"model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "max_length": 512, "replicas": 2,
                 "batch": "todos los candidatos en un lote"},
    "timeouts_ms": {"lexical": 50, "semantic": 1200, "fusion": 50, "rerank": 1200},
    "slo_ms": 2500,
    "hedging": {"threshold": "p95 del reranker medido en calibración", "max_extra": 0.10, "window_s": 60},
}

# Values that alpha.json must carry (the frozen block above, in alpha.json's own vocabulary).
ALPHA_EXPECTED = {
    "alpha": 0.85,
    "model": CONFIG["semantic"]["model"],
    "model_revision": CONFIG["semantic"]["model_revision"],
    "normalization": "per-query candidate min-max; constant scores -> 1.0",
    "document_tie_break": "ascending document ID (string)",
    "bm25": {"library": "bm25s", "method": "lucene", "k1": 0.9, "b": 0.4, "stopwords": "en",
             "stemmer": "english (PyStemmer)", "top_k": 10},
    "semantic": {"query_prefix": CONFIG["semantic"]["query_prefix"], "max_length": 512, "normalize": True,
                 "index": "faiss.IndexFlatIP", "top_k": 10},
}

# Interpretations of points the spec leaves open; copied into run_meta.json for the paper.
INTERPRETATIONS = {
    "replica_model": "each stage/replica runs on its own ThreadPoolExecutor (lex 2 workers, sem 1, fusion 2, "
                     "rerank_a 1, rerank_b 1); both reranker replicas share the same GPU",
    "delay_injection": "the stage computes its result, then awaits asyncio.sleep(delay) before responding; "
                       "the worker thread is not blocked by the injected delay",
    "error_injection": "the stage raises immediately, without computing",
    "expired_work": "work whose stage deadline already passed when it reaches a worker is skipped",
    "hedge_trigger": "replica B is sent when A has no valid answer at the threshold (pending or failed) and "
                     "hedges in the last 60 s < 10% of originals in the last 60 s",
    "arrivals": "Poisson inter-arrivals from np.random.default_rng(42), identical for every condition with "
                "the same rate and for every repetition",
    "delay_draws": "np.random.default_rng([42, rep, request_index]).random(4) -> lex, sem, rerank_a, rerank_b",
    "fusion_failure": "if fusion fails or exceeds 50 ms the lexical top 3 is returned (route lex)",
    "capacity_throughput": "throughput ratio = responses with route=reranked, 3 results and latency <= SLO "
                           "divided by the requests actually sent in the step (Poisson arrivals make the sent "
                           "count differ from the nominal rate); all ramp steps run and C is the highest "
                           "passing rate",
    "calibration_hedging": "calibration (a) runs with hedging off (threshold unknown); ramp (b) with hedging on",
    "hedge_latency": "the 1.2 s rerank deadline is shared by both replicas; a hedge sent after the deadline "
                     "cannot win and its latency equals the stage duration (compute + injected delay), so it "
                     "may exceed the stage deadline",
    "top_k_tie_break": "lexical and semantic top 10 also break score ties by ascending document ID",
}

ROUTES = ["reranked", "fused_baseline", "fused_fallback", "lex", "sem", "error"]
STAGES = ["lex", "sem", "fusion", "rerank"]
RAMP_RATES = [1, 2, 4, 8, 16, 32, 64]

# name, load fraction of C, faults, hedging, rerank enabled
CONDITIONS = [
    ("L25", 0.25, {}, True, True),
    ("L50", 0.50, {}, True, True),
    ("L75", 0.75, {}, True, True),
    ("L100", 1.00, {}, True, True),
    ("NORERANK", 1.00, {}, False, False),
    ("NOHEDGE", 1.00, {}, False, True),
    ("F1", 0.75, {"rerank_a": "error", "rerank_b": "error"}, True, True),
    ("F2", 0.75, {"rerank_a": "delay:1500", "rerank_b": "delay:1500"}, True, True),
    ("F3H", 0.75, {"rerank_a": "delay_prob:0.05:800"}, True, True),
    ("F3NH", 0.75, {"rerank_a": "delay_prob:0.05:800"}, False, True),
    ("F4", 0.75, {"sem": "error"}, True, True),
    ("F5", 0.75, {"lex": "error"}, True, True),
    ("F6", 0.75, {"lex": "error", "sem": "error"}, True, True),
]

pc = time.perf_counter


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


class InjectedError(RuntimeError):
    pass


class Expired(RuntimeError):
    pass


def p_ceil(values, q):
    """Paper percentile: sort N values and take position ceil(q * N) (1-based)."""
    if len(values) == 0:
        return None
    v = np.sort(np.asarray(values, dtype=float))
    return float(v[max(1, math.ceil(q * len(v))) - 1])


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------------- alpha
def load_alpha(path):
    alpha = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    for key, expected in ALPHA_EXPECTED.items():
        got = alpha.get(key)
        if isinstance(expected, dict):
            got = got or {}
            errors += [f"{key}.{k}: {got.get(k)!r} != {v!r}" for k, v in expected.items() if got.get(k) != v]
        elif got != expected:
            errors.append(f"{key}: {got!r} != {expected!r}")
    if errors:
        sys.exit("alpha.json does not match the frozen configuration:\n  " + "\n  ".join(errors))
    return alpha


# ----------------------------------------------------------------------------- data
def load_dataset(name, data_dir):
    data_dir = Path(data_dir)
    root = data_dir / name
    if not (root / "corpus.jsonl").exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        zpath = data_dir / f"{name}.zip"
        if not zpath.exists():
            log(f"downloading {CONFIG['datasets'][name]}")
            try:
                urllib.request.urlretrieve(CONFIG["datasets"][name], zpath)
            except Exception as e:
                log(f"urllib failed ({e}); retrying with curl")
                subprocess.run(["curl", "-sSfL", "-o", str(zpath), CONFIG["datasets"][name]], check=True)
        with zipfile.ZipFile(zpath) as z:
            z.extractall(data_dir)

    def jsonl(p):
        with open(p, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def qrels(split):
        p = root / "qrels" / f"{split}.tsv"
        if not p.exists():
            return []
        qids = []
        with open(p, encoding="utf-8") as f:
            next(f)
            for line in f:
                qid = line.split("\t")[0]
                if not qids or qids[-1] != qid:
                    qids.append(qid)
        return list(dict.fromkeys(qids))

    corpus = jsonl(root / "corpus.jsonl")
    queries = {str(q["_id"]): q["text"] for q in jsonl(root / "queries.jsonl")}
    return corpus, queries, qrels("train"), qrels("test")


def build_query_sets(name, corpus, queries, train_qids, test_qids):
    rng = np.random.default_rng(CONFIG["seed"])
    test = [(qid, queries[qid]) for qid in test_qids if qid in queries]
    if name == "fiqa":
        calib = [(qid, queries[qid]) for qid in train_qids if qid in queries]
        calib = [calib[i] for i in rng.permutation(len(calib))]
    else:
        titled = [d for d in corpus if (d.get("title") or "").strip()]
        pick = rng.choice(len(titled), size=min(1000, len(titled)), replace=False)
        calib = [(f"title:{titled[i]['_id']}", titled[i]["title"].strip()) for i in pick]
    return calib, test


# ----------------------------------------------------------------------------- engine
def topk_tiebreak(scores, k, id_rank):
    n = len(scores)
    k = min(k, n)
    if k == n:
        idx = np.arange(n)
    else:
        kth = np.partition(scores, n - k)[n - k]
        gt = np.flatnonzero(scores > kth)
        eq = np.flatnonzero(scores == kth)
        need = k - len(gt)
        if len(eq) > need:
            eq = eq[np.argpartition(id_rank[eq], need - 1)[:need]] if need > 0 else eq[:0]
        idx = np.concatenate([gt, eq])
    return idx[np.lexsort((id_rank[idx], -scores[idx]))]


def minmax(x):
    lo, hi = x.min(), x.max()
    return np.ones_like(x) if hi == lo else (x - lo) / (hi - lo)


class Engine:
    def __init__(self, corpus, alpha, device, encode_batch):
        import bm25s
        import faiss
        import Stemmer
        import torch
        from sentence_transformers import CrossEncoder, SentenceTransformer

        self.torch, self.bm25s, self.Stemmer = torch, bm25s, Stemmer
        self.alpha = float(alpha)
        self.doc_ids = [str(d["_id"]) for d in corpus]
        self.texts = [f"{d.get('title') or ''} {d.get('text') or ''}" for d in corpus]
        order = sorted(range(len(self.doc_ids)), key=lambda i: self.doc_ids[i])
        self.id_rank = np.empty(len(order), dtype=np.int64)
        self.id_rank[order] = np.arange(len(order))
        self._local = threading.local()
        self.timings = {}

        t = pc()
        tokens = bm25s.tokenize(self.texts, stopwords="en", stemmer=self._stemmer(), show_progress=False)
        self.bm25 = bm25s.BM25(method="lucene", k1=0.9, b=0.4)
        self.bm25.index(tokens, show_progress=False)
        self.timings["bm25_index_s"] = pc() - t
        log(f"BM25 index: {len(self.texts)} docs in {self.timings['bm25_index_s']:.1f}s")

        sem = CONFIG["semantic"]
        self.encoder = SentenceTransformer(sem["model"], revision=sem["model_revision"], device=device)
        self.encoder.max_seq_length = sem["max_length"]
        pooling = self.encoder[1]
        assert getattr(pooling, "pooling_mode_cls_token", False) or getattr(pooling, "pooling_mode", None) == "cls", \
            "bge pooling must be CLS"
        if device.startswith("cuda"):
            self.encoder.half()
        t = pc()
        self.emb = self._encode(self.texts, encode_batch)
        self.timings["corpus_encode_s"] = pc() - t
        log(f"corpus embeddings {self.emb.shape} in {self.timings['corpus_encode_s']:.1f}s")
        self.index = faiss.IndexFlatIP(self.emb.shape[1])
        self.index.add(self.emb)

        rr = CONFIG["reranker"]
        self.rerankers = {r: CrossEncoder(rr["model"], max_length=rr["max_length"], device=device) for r in "ab"}

    def _stemmer(self):
        if not hasattr(self._local, "stemmer"):
            self._local.stemmer = self.Stemmer.Stemmer("english")
        return self._local.stemmer

    def _encode(self, texts, batch_size):
        with self.torch.inference_mode():
            e = self.encoder.encode(texts, batch_size=batch_size, convert_to_tensor=True,
                                    normalize_embeddings=False, show_progress_bar=False)
            e = self.torch.nn.functional.normalize(e.float(), dim=-1)
        return np.ascontiguousarray(e.cpu().numpy(), dtype=np.float32)

    def lex(self, q):
        toks = self.bm25s.tokenize([q], stopwords="en", stemmer=self._stemmer(), return_ids=False,
                                   show_progress=False)[0]
        scores = np.asarray(self.bm25.get_scores(toks), dtype=np.float32) if toks else \
            np.zeros(len(self.doc_ids), dtype=np.float32)
        return topk_tiebreak(scores, CONFIG["lexical"]["top_k"], self.id_rank), scores

    def sem(self, q):
        qe = self._encode([CONFIG["semantic"]["query_prefix"] + q], 1)
        k = min(CONFIG["semantic"]["top_k"], len(self.doc_ids))
        scores, idx = self.index.search(qe, k)
        idx, scores = idx[0], scores[0]
        return idx[np.lexsort((self.id_rank[idx], -scores))], qe[0]

    def fuse(self, lex_top, lex_scores, sem_top, qemb):
        cand = np.unique(np.concatenate([lex_top, sem_top]))
        lex_n = minmax(lex_scores[cand].astype(np.float64))
        sem_n = minmax((self.emb[cand] @ qemb).astype(np.float64))
        fused = (1 - self.alpha) * lex_n + self.alpha * sem_n
        return cand[np.lexsort((self.id_rank[cand], -fused))]

    def rerank(self, rid, q, cand):
        pairs = [(q, self.texts[i]) for i in cand]
        with self.torch.inference_mode():
            s = np.asarray(self.rerankers[rid].predict(pairs, batch_size=len(pairs), show_progress_bar=False),
                           dtype=np.float64)
        return cand[np.lexsort((self.id_rank[cand], -s))][:3]


# ----------------------------------------------------------------------------- service
def parse_mode(mode):
    if mode in ("ok", "error"):
        return mode, 0.0, 0.0
    parts = mode.split(":")
    if parts[0] == "delay":
        return "delay", 1.0, float(parts[1]) / 1000
    if parts[0] == "delay_prob":
        return "delay", float(parts[1]), float(parts[2]) / 1000
    raise ValueError(f"unknown fault mode {mode}")


class Service:
    def __init__(self, engine):
        self.engine = engine
        self.ex = {"lex": ThreadPoolExecutor(2, "lex"), "sem": ThreadPoolExecutor(1, "sem"),
                   "fusion": ThreadPoolExecutor(2, "fusion"),
                   "rerank_a": ThreadPoolExecutor(1, "rra"), "rerank_b": ThreadPoolExecutor(1, "rrb")}
        self.threshold_s = None
        self.reset_hedge_window()

    def reset_hedge_window(self):
        self.orig_times, self.hedge_times = deque(), deque()

    def hedge_allowed(self, now):
        w = CONFIG["hedging"]["window_s"]
        for dq in (self.orig_times, self.hedge_times):
            while dq and dq[0] < now - w:
                dq.popleft()
        return len(self.hedge_times) < CONFIG["hedging"]["max_extra"] * len(self.orig_times)

    async def run_in(self, name, deadline, fn, *args):
        def job():
            if pc() > deadline:
                raise Expired(name)
            return fn(*args)
        return await asyncio.get_running_loop().run_in_executor(self.ex[name], job)

    async def component(self, name, executor, mode, draw, deadline, flags, fn, *args):
        kind, prob, delay = parse_mode(mode)
        if kind == "error":
            raise InjectedError(name)
        res = await self.run_in(executor, deadline, fn, *args)
        if kind == "delay" and draw < prob:
            flags["delay"] = True
            await asyncio.sleep(delay)
        return res

    async def stage(self, name, timeout_s, coro_fn):
        t0 = pc()
        try:
            res = await asyncio.wait_for(coro_fn(t0 + timeout_s), timeout_s)
            status = "ok"
        except asyncio.TimeoutError:
            res, status = None, "timeout"
        except Exception:
            res, status = None, "error"
        return res, status, (pc() - t0) * 1000

    async def rerank_hedged(self, q, cand, faults, draws, hedging, flags):
        t0 = pc()
        deadline = t0 + CONFIG["timeouts_ms"]["rerank"] / 1000
        self.orig_times.append(t0)

        def launch(rid):
            key = f"rerank_{rid}"
            task = asyncio.create_task(self.component(key, key, faults.get(key, "ok"), draws[key], deadline,
                                                      flags, self.engine.rerank, rid, q, cand))
            task.add_done_callback(lambda t: t.cancelled() or t.exception())
            tasks[task] = rid
            return task

        def harvest(done):
            for t in done:
                if not t.cancelled() and t.exception() is None:
                    return t.result(), tasks[t]
            return None, None

        tasks = {}
        launch("a")
        result, winner, hedge_sent = None, None, False
        if hedging and self.threshold_s is not None:
            done, _ = await asyncio.wait(list(tasks), timeout=max(0.0, min(self.threshold_s, deadline - pc())))
            result, winner = harvest(done)
            now = pc()
            if result is None and now < deadline and self.hedge_allowed(now):
                self.hedge_times.append(now)
                hedge_sent = True
                launch("b")
        while result is None:
            pending = [t for t in tasks if not t.done()]
            remaining = deadline - pc()
            if not pending or remaining <= 0:
                break
            done, _ = await asyncio.wait(pending, timeout=remaining, return_when=asyncio.FIRST_COMPLETED)
            result, winner = harvest(done)
        for t in tasks:
            t.cancel()
        all_failed = all(t.done() and not t.cancelled() and t.exception() is not None for t in tasks)
        status = "ok" if result is not None else ("error" if all_failed else "timeout")
        return result, status, (pc() - t0) * 1000, hedge_sent, winner == "b"

    async def handle(self, ctx, i, qid, q, t_sched_abs):
        cond, rep, faults = ctx["condition"], ctx["rep"], ctx["faults"]
        draws = dict(zip(["lex", "sem", "rerank_a", "rerank_b"], np.random.default_rng([42, rep, i]).random(4)))
        flags = {"delay": False}
        to = CONFIG["timeouts_ms"]
        stage_ms = {s: None for s in STAGES}
        timeouts, errors = [], []

        def note(name, status, ms):
            stage_ms[name] = round(ms, 3)
            if status == "timeout":
                timeouts.append(name)
            elif status == "error":
                errors.append(name)

        lex_job = lambda dl: self.component("lex", "lex", faults.get("lex", "ok"), draws["lex"], dl, flags,
                                            self.engine.lex, q)
        sem_job = lambda dl: self.component("sem", "sem", faults.get("sem", "ok"), draws["sem"], dl, flags,
                                            self.engine.sem, q)
        (lex_res, lex_st, lex_ms), (sem_res, sem_st, sem_ms) = await asyncio.gather(
            self.stage("lex", to["lexical"] / 1000, lex_job), self.stage("sem", to["semantic"] / 1000, sem_job))
        note("lex", lex_st, lex_ms)
        note("sem", sem_st, sem_ms)

        doc_idx, route, rerank_invoked, hedge_sent, hedge_won = [], "error", False, False, False
        if lex_res is not None and sem_res is not None:
            fus_job = lambda dl: self.run_in("fusion", dl, self.engine.fuse, lex_res[0], lex_res[1], sem_res[0],
                                             sem_res[1])
            fused, fus_st, fus_ms = await self.stage("fusion", to["fusion"] / 1000, fus_job)
            note("fusion", fus_st, fus_ms)
            if fused is None:
                doc_idx, route = lex_res[0][:3], "lex"
            elif not ctx["rerank"]:
                doc_idx, route = fused[:3], "fused_baseline"
            else:
                rerank_invoked = True
                top3, rr_st, rr_ms, hedge_sent, hedge_won = await self.rerank_hedged(
                    q, fused, faults, draws, ctx["hedging"], flags)
                note("rerank", rr_st, rr_ms)
                doc_idx, route = (top3, "reranked") if top3 is not None else (fused[:3], "fused_fallback")
        elif lex_res is not None:
            doc_idx, route = lex_res[0][:3], "lex"
        elif sem_res is not None:
            doc_idx, route = sem_res[0][:3], "sem"

        t_end = pc()
        return {"dataset": ctx["dataset"], "rep": rep, "condition": cond, "qid": qid,
                "t_sched": round(t_sched_abs - ctx["t0"], 6), "t_end": round(t_end - ctx["t0"], 6),
                "latency_ms": round((t_end - t_sched_abs) * 1000, 3), "route": route,
                "n_results": len(doc_idx), "timeouts": timeouts, "errors": errors,
                "rerank_invoked": rerank_invoked, "delay_injected": flags["delay"], "hedge_sent": hedge_sent,
                "hedge_won": hedge_won, "stage_ms": stage_ms,
                "doc_ids": [self.engine.doc_ids[j] for j in doc_idx]}

    async def run_load(self, ctx, queries, rate, duration_s=None, n_requests=None, out_path=None):
        rng = np.random.default_rng(CONFIG["seed"])
        times, t = [], 0.0
        while True:
            t += rng.exponential(1.0 / rate)
            if (duration_s is not None and t >= duration_s) or (n_requests is not None and len(times) >= n_requests):
                break
            times.append(t)
        self.reset_hedge_window()
        ctx["t0"] = pc() + 0.2
        tasks = []
        for i, ts in enumerate(times):
            wait = ctx["t0"] + ts - pc()
            if wait > 0:
                await asyncio.sleep(wait)
            qid, q = queries[i % len(queries)]
            tasks.append(asyncio.create_task(self.handle(ctx, i, qid, q, ctx["t0"] + ts)))
        records = await asyncio.gather(*tasks)
        if out_path:
            with open(out_path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")
        await asyncio.sleep(2.0)
        return records


# ----------------------------------------------------------------------------- metrics
def summarize(records, warmup_s, window_s):
    recs = [r for r in records if r["t_sched"] >= warmup_s]
    n = len(recs)
    valid = [r["latency_ms"] for r in recs if r["n_results"] == 3]
    slo = CONFIG["slo_ms"]
    invoked = sum(r["rerank_invoked"] for r in recs)
    hedges = sum(r["hedge_sent"] for r in recs)
    pct = lambda x: round(100.0 * x / n, 4) if n else None
    row = {"n_sent": n, "n_valid": len(valid),
           "qps_offered_measured": round(n / window_s, 4) if window_s > 0 else None,
           "qps_achieved": round(len(valid) / window_s, 4) if window_s > 0 else None,
           "p50_ms": p_ceil(valid, 0.50), "p95_ms": p_ceil(valid, 0.95), "p99_ms": p_ceil(valid, 0.99),
           "error_pct": pct(sum(r["route"] == "error" for r in recs)),
           "continuity_pct": pct(sum(r["n_results"] == 3 and r["latency_ms"] <= slo for r in recs)),
           "rerank_originals": invoked, "hedge_sent": hedges,
           "hedge_won": sum(r["hedge_won"] for r in recs),
           "dup_pct": round(100.0 * hedges / invoked, 4) if invoked else None}
    for s in STAGES:
        row[f"timeout_pct_{s}"] = pct(sum(s in r["timeouts"] for r in recs))
        row[f"errorstage_pct_{s}"] = pct(sum(s in r["errors"] for r in recs))
    for route in ROUTES:
        row[f"route_pct_{route}"] = pct(sum(r["route"] == route for r in recs))
    return row


def stage_percentiles(records):
    out = {}
    for s in STAGES + ["e2e"]:
        vals = [r["latency_ms"] if s == "e2e" else r["stage_ms"][s] for r in records]
        vals = [v for v in vals if v is not None]
        out[s] = {"n": len(vals), "p50_ms": p_ceil(vals, 0.50), "p95_ms": p_ceil(vals, 0.95),
                  "p99_ms": p_ceil(vals, 0.99)}
    return out


def ramp_step_ok(records, rate, step_s):
    slo = CONFIG["slo_ms"]
    good = [r for r in records if r["route"] == "reranked" and r["n_results"] == 3 and r["latency_ms"] <= slo]
    n = len(records)
    ratio = len(good) / n if n else 0.0
    lat = lambda rs: [r["latency_ms"] for r in rs if r["n_results"] == 3]
    first = p_ceil(lat([r for r in records if r["t_sched"] < step_s / 2]), 0.99)
    second = p_ceil(lat([r for r in records if r["t_sched"] >= step_s / 2]), 0.99)
    stable = first is not None and second is not None and second <= 1.2 * first
    return {"rate": rate, "n_sent": n, "qps_offered_measured": round(n / step_s, 4),
            "qps_achieved": round(len(good) / step_s, 4), "throughput_ratio": round(ratio, 4),
            "p99_ms": p_ceil(lat(records), 0.99), "p99_first_half_ms": first, "p99_second_half_ms": second,
            "p99_stable": stable, "pass": ratio >= 0.99 and stable}


# ----------------------------------------------------------------------------- meta
def run_cmd(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except Exception as e:
        return f"unavailable: {e}"


def library_versions():
    import importlib.metadata as md
    out = {}
    for pkg in ["torch", "sentence-transformers", "transformers", "faiss-cpu", "bm25s", "PyStemmer", "numpy",
                "scipy", "huggingface-hub", "tokenizers"]:
        try:
            out[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            out[pkg] = None
    return out


def model_shas():
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        return {"reranker": api.model_info(CONFIG["reranker"]["model"]).sha,
                "semantic_pinned": CONFIG["semantic"]["model_revision"]}
    except Exception as e:
        return {"error": str(e)}


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


# ----------------------------------------------------------------------------- main
async def main_async(args):
    random.seed(CONFIG["seed"])
    np.random.seed(CONFIG["seed"])
    out = Path(args.out) / args.dataset
    out.mkdir(parents=True, exist_ok=True)
    alpha = load_alpha(args.alpha)
    log(f"alpha.json OK (alpha={alpha['alpha']})")

    import torch
    torch.manual_seed(CONFIG["seed"])
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    pilot = args.pilot
    max_docs = args.max_docs or (2000 if pilot else None)
    cond_s = args.cond_seconds or (60 if pilot else 180)
    warmup_s = args.warmup_seconds if args.warmup_seconds is not None else (15 if pilot else 30)
    ramp_s = args.ramp_seconds or (20 if pilot else 120)
    calib_n = args.calib_n or (60 if pilot else 500)
    ramp_rates = [float(r) for r in args.ramp_rates.split(",")] if args.ramp_rates else RAMP_RATES
    reps = args.reps or (1 if pilot else 3)
    conditions = [c for c in CONDITIONS if not args.conditions or c[0] in args.conditions.split(",")]

    meta = {"dataset": args.dataset, "argv": sys.argv, "pilot": pilot, "device": device,
            "node": platform.node(), "platform": platform.platform(), "python": sys.version,
            "nvidia_smi": run_cmd(["nvidia-smi"]), "lscpu": run_cmd(["lscpu"]),
            "libraries": library_versions(), "model_shas": model_shas(),
            "script_sha256": sha256_file(__file__), "config": CONFIG, "interpretations": INTERPRETATIONS,
            "alpha_json": alpha,
            "settings": {"max_docs": max_docs, "cond_seconds": cond_s, "warmup_seconds": warmup_s,
                         "ramp_seconds": ramp_s, "calib_n": calib_n, "ramp_rates": ramp_rates, "reps": reps,
                         "conditions": [c[0] for c in conditions]},
            "env": {k: os.environ.get(k) for k in ["CUDA_VISIBLE_DEVICES", "KAGGLE_KERNEL_RUN_TYPE",
                                                   "SLURM_JOB_ID", "HF_HUB_OFFLINE"]}}
    if device.startswith("cuda"):
        meta["gpu"] = torch.cuda.get_device_name(0)
    write_json(out / "run_meta.json", meta)

    # Phase 0
    t_phase0 = pc()
    corpus, queries, train_qids, test_qids = load_dataset(args.dataset, args.data_dir)
    if max_docs and len(corpus) > max_docs:
        keep = np.sort(np.random.default_rng(CONFIG["seed"]).choice(len(corpus), size=max_docs, replace=False))
        corpus = [corpus[i] for i in keep]
    calib_q, test_q = build_query_sets(args.dataset, corpus, queries, train_qids, test_qids)
    log(f"{args.dataset}: {len(corpus)} docs, {len(test_q)} test queries, {len(calib_q)} calibration queries")
    engine = Engine(corpus, alpha["alpha"], device, args.encode_batch)
    service = Service(engine)
    log("warm-up: 50 queries")
    for qid, q in calib_q[:50]:
        lex_res, sem_res = engine.lex(q), engine.sem(q)
        cand = engine.fuse(lex_res[0], lex_res[1], sem_res[0], sem_res[1])
        engine.rerank("a", q, cand)
        engine.rerank("b", q, cand)
    meta["phase0_seconds"] = pc() - t_phase0
    meta["index_timings"] = engine.timings
    meta["corpus_size"] = len(corpus)
    meta["n_test_queries"], meta["n_calibration_queries"] = len(test_q), len(calib_q)

    base_ctx = {"dataset": args.dataset, "faults": {}, "rerank": True}

    # Phase 1
    if args.calibration:
        calibration = json.loads(Path(args.calibration).read_text(encoding="utf-8"))
        log(f"loaded frozen calibration: C={calibration['C_qps']} threshold={calibration['hedge_threshold_ms']}ms")
    else:
        log(f"calibration (a): {calib_n} queries at 1 QPS, hedging off")
        recs = await service.run_load(dict(base_ctx, condition="CALIB_1QPS", rep=0, hedging=False), calib_q, 1.0,
                                      n_requests=calib_n, out_path=out / f"requests_{args.dataset}_calib_1qps.jsonl")
        stages = stage_percentiles(recs)
        threshold_ms = stages["rerank"]["p95_ms"]
        service.threshold_s = threshold_ms / 1000
        log(f"stage percentiles: {json.dumps(stages)}")
        log(f"hedging threshold = p95 rerank = {threshold_ms:.1f} ms")
        steps, C = [], None
        for rate in ramp_rates:
            recs = await service.run_load(dict(base_ctx, condition=f"RAMP_{rate:g}", rep=0, hedging=True),
                                          calib_q, rate, duration_s=ramp_s,
                                          out_path=out / f"requests_{args.dataset}_ramp_{rate:g}.jsonl")
            step = ramp_step_ok(recs, rate, ramp_s)
            steps.append(step)
            log(f"ramp {rate:g} QPS: {json.dumps(step)}")
            if step["pass"]:
                C = rate
            if len(steps) >= 2 and not steps[-1]["pass"] and not steps[-2]["pass"]:
                break
        if C is None:
            write_json(out / "calibration.json", {"stages_1qps": stages, "ramp": steps, "C_qps": None})
            sys.exit("calibration failed: no ramp step met the capacity criterion")
        calibration = {"frozen": True, "dataset": args.dataset, "stages_1qps": stages,
                       "hedge_threshold_ms": threshold_ms, "ramp": steps, "ramp_seconds": ramp_s, "C_qps": C,
                       "capacity_rule": "highest ramp rate (all steps are run) with throughput >= 99% of the "
                                        "requests actually sent and p99(second half) <= 1.2 * p99(first half)",
                       "throughput_definition": INTERPRETATIONS["capacity_throughput"]}
        write_json(out / "calibration.json", calibration)
        log(f"capacity C = {C} QPS (calibration.json frozen)")
    service.threshold_s = calibration["hedge_threshold_ms"] / 1000
    meta["calibration"] = calibration
    write_json(out / "run_meta.json", meta)
    if args.phase == "calibrate":
        return

    # Phase 2
    C = calibration["C_qps"]
    summary_path = out / "summary.csv"
    rows = []
    for rep in range(1, reps + 1):
        for name, frac, faults, hedging, rerank in conditions:
            rate = frac * C
            log(f"rep {rep} {name}: {rate:.3f} QPS for {cond_s}s, faults={faults}, hedging={hedging}")
            ctx = {"dataset": args.dataset, "condition": name, "rep": rep, "faults": faults, "hedging": hedging,
                   "rerank": rerank}
            recs = await service.run_load(ctx, test_q, rate, duration_s=cond_s,
                                          out_path=out / f"requests_{args.dataset}_rep{rep}_{name}.jsonl")
            row = {"dataset": args.dataset, "rep": rep, "condition": name, "load_pct": int(frac * 100),
                   "qps_offered": round(rate, 4), "hedging": hedging, "rerank_enabled": rerank,
                   "faults": json.dumps(faults), **summarize(recs, warmup_s, cond_s - warmup_s)}
            rows.append(row)
            log(f"  -> p99={row['p99_ms']} continuity={row['continuity_pct']}% dup={row['dup_pct']}% "
                f"routes={ {r: row[f'route_pct_{r}'] for r in ROUTES if row[f'route_pct_{r}']} }")
            with open(summary_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
    meta["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    write_json(out / "run_meta.json", meta)
    log("done")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", required=True, choices=list(CONFIG["datasets"]))
    ap.add_argument("--reps", type=int)
    ap.add_argument("--out", default="results")
    ap.add_argument("--alpha", default=str(Path(__file__).with_name("alpha.json")))
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--device")
    ap.add_argument("--pilot", action="store_true", help="2,000 docs, 1 min per condition, 1 repetition")
    ap.add_argument("--phase", choices=["all", "calibrate"], default="all")
    ap.add_argument("--calibration", help="frozen calibration.json to reuse (skips phase 1)")
    ap.add_argument("--conditions", help="comma-separated subset of conditions")
    ap.add_argument("--max-docs", type=int)
    ap.add_argument("--cond-seconds", type=float)
    ap.add_argument("--warmup-seconds", type=float)
    ap.add_argument("--ramp-seconds", type=float)
    ap.add_argument("--ramp-rates")
    ap.add_argument("--calib-n", type=int)
    ap.add_argument("--encode-batch", type=int, default=64)
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
