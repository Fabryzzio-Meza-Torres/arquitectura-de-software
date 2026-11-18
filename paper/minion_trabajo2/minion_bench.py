#!/usr/bin/env python3
"""
minion_bench.py — Trabajos 2/3 del paper MINION (latencia y fallas en Khipu).

Un solo proceso con asyncio. Cada etapa (lex, sem, fusion, rerank) corre su trabajo
pesado en un ThreadPoolExecutor. Carga open-loop (Poisson). Solo mide TIEMPO y CONTINUIDAD
(la calidad P@3 se calcula en el Trabajo 1).

Uso típico:
  # laptop (subconjunto, ~15 min):
  python minion_bench.py --dataset fiqa --subset 2000 --quick --out results_laptop
  # job real en Khipu:
  python minion_bench.py --dataset fiqa --reps 3 --out results/
  # solo probar la lógica sin modelos:
  python minion_bench.py --dataset fiqa --fake --quick --out results_fake
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import concurrent.futures as cf
import csv
import functools
import gc
import hashlib
import importlib.metadata as md
import json
import math
import os
import platform
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
import zlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np

# --------------------------------------------------------------------------------------
# Configuración CONGELADA (sección 2 de la especificación). No cambiar.
# --------------------------------------------------------------------------------------
SEED = 42
DATASET_URLS = {
    "fiqa": "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/fiqa.zip",
    "trec-covid": "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/trec-covid.zip",
}
LEX = {"lib": "bm25s", "method": "lucene", "k1": 0.9, "b": 0.4, "stopwords": "en",
       "stemmer": "english (PyStemmer)", "top_k": 10}
SEM_MODEL = "BAAI/bge-base-en-v1.5"
SEM_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
SEM_MAXLEN = 512
SEM_TOPK = 10
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RERANK_MAXLEN = 512
LEX_TO, SEM_TO, FUS_TO, RERANK_TO = 0.050, 1.200, 0.050, 1.200  # segundos
SLO_MS = 2500.0
HEDGE_MAX_EXTRA = 0.10
HEDGE_WINDOW_S = 60.0
ALPHA_EXPECTED = 0.85
NORMALIZATION = "per-query candidate min-max; constant scores -> 1.0"
TIE_BREAK = "ascending document ID (string)"
ROUTES = ["reranked", "fused_baseline", "fused_fallback", "lex", "sem", "error"]
STAGES = ["lex", "sem", "fusion", "rerank"]

FROZEN_CONFIG = {
    "seed": SEED, "datasets": DATASET_URLS, "doc_text": "title + ' ' + text", "lexical": LEX,
    "semantic": {"model": SEM_MODEL, "model_revision": SEM_REVISION, "query_prefix": QUERY_PREFIX,
                 "encoding": "forward fp16; CLS pooling; L2; float32", "index": "faiss.IndexFlatIP",
                 "max_length": SEM_MAXLEN, "top_k": SEM_TOPK},
    "fusion": {"normalization": NORMALIZATION, "formula": "(1 - alpha) * lex_norm + alpha * sem_norm",
               "alpha": "alpha.json", "tie_break": TIE_BREAK},
    "reranker": {"model": RERANK_MODEL, "max_length": RERANK_MAXLEN, "replicas": 2,
                 "batch": "todos los candidatos en un lote"},
    "timeouts_ms": {"lexical": 50, "semantic": 1200, "fusion": 50, "rerank": 1200},
    "slo_ms": SLO_MS,
    "hedging": {"threshold": "p95 del reranker en calibración", "max_extra": HEDGE_MAX_EXTRA,
                "window_s": HEDGE_WINDOW_S},
}


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


# --------------------------------------------------------------------------------------
# Condiciones (sección 4)
# --------------------------------------------------------------------------------------
class Cond(SimpleNamespace):
    pass


def make_conditions():
    C = lambda name, load, hedging=True, rerank=True, faults=None: Cond(
        name=name, load=load, hedging=hedging, rerank=rerank, faults=faults or {})
    return [
        C("L25", 0.25), C("L50", 0.50), C("L75", 0.75), C("L100", 1.00),
        C("NORERANK", 1.00, rerank=False),
        C("NOHEDGE", 1.00, hedging=False),
        C("F1", 0.75, faults={"rerank_a": "error", "rerank_b": "error"}),
        C("F2", 0.75, faults={"rerank_a": "delay:1500", "rerank_b": "delay:1500"}),
        C("F3H", 0.75, faults={"rerank_a": "delay_prob:0.05:800"}),
        C("F3NH", 0.75, hedging=False, faults={"rerank_a": "delay_prob:0.05:800"}),
        C("F4", 0.75, faults={"sem": "error"}),
        C("F5", 0.75, faults={"lex": "error"}),
        C("F6", 0.75, faults={"lex": "error", "sem": "error"}),
    ]


# --------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------
def pctl(vals, q):
    """Método del paper: ordenar los N tiempos y tomar la posición ceil(q/100 * N)."""
    if len(vals) == 0:
        return float("nan")
    s = sorted(vals)
    n = len(s)
    return float(s[max(0, math.ceil(round(q * n / 100.0, 9)) - 1)])


def minmax(x):
    mn, mx = float(x.min()), float(x.max())
    if mx == mn:
        return np.ones_like(x, dtype=np.float64)
    return (x - mn) / (mx - mn)


def topk_tiebreak(scores, id_rank, k):
    """Top-k por puntaje desc; empates por ID ascendente (como string), también en el corte."""
    n = len(scores)
    if n <= k:
        cand = np.arange(n)
    else:
        kth = np.partition(scores, n - k)[n - k]
        cand = np.flatnonzero(scores >= kth)
    order = np.lexsort((id_rank[cand], -scores[cand]))
    return cand[order][:k]


def poisson_arrivals(qps, rng, duration=None, n=None):
    ts, t = [], 0.0
    while True:
        t += rng.exponential(1.0 / qps)
        if duration is not None and t >= duration:
            break
        ts.append(t)
        if n is not None and len(ts) >= n:
            break
    return ts


def draws(rep, idx):
    """Números deterministas por (rep, solicitud): F3H y F3NH demoran exactamente las mismas."""
    rng = np.random.default_rng([SEED, rep, idx])
    v = rng.random(4)
    return dict(zip(("lex", "sem", "rerank_a", "rerank_b"), v.tolist()))


async def apply_fault(mode, u, rec):
    """Marca delay_injected ANTES de dormir (si la demora se cancela, igual queda registrada).
    Lanza excepción si el modo es 'error'."""
    if not mode or mode == "ok":
        return
    if mode == "error":
        raise RuntimeError("injected_error")
    parts = mode.split(":")
    if parts[0] == "delay":
        rec["delay_injected"] = True
        await asyncio.sleep(float(parts[1]) / 1000.0)
        return
    if parts[0] == "delay_prob":
        if u < float(parts[1]):
            rec["delay_injected"] = True
            await asyncio.sleep(float(parts[2]) / 1000.0)
        return
    raise ValueError(f"modo de falla desconocido: {mode}")


# --------------------------------------------------------------------------------------
# alpha.json: verificación al arrancar
# --------------------------------------------------------------------------------------
def load_and_check_alpha(path):
    a = json.load(open(path))
    errs = []
    if a.get("alpha") != ALPHA_EXPECTED:
        errs.append(f"alpha={a.get('alpha')} (esperado {ALPHA_EXPECTED})")
    exp_bm25 = {"library": "bm25s", "method": "lucene", "k1": 0.9, "b": 0.4, "stopwords": "en",
                "stemmer": "english (PyStemmer)", "top_k": 10}
    for k, v in exp_bm25.items():
        if a.get("bm25", {}).get(k) != v:
            errs.append(f"bm25.{k}={a.get('bm25', {}).get(k)} (esperado {v})")
    if a.get("semantic", {}).get("query_prefix") != QUERY_PREFIX:
        errs.append("semantic.query_prefix difiere")
    if a.get("semantic", {}).get("max_length") != SEM_MAXLEN:
        errs.append("semantic.max_length difiere")
    if a.get("semantic", {}).get("top_k") != SEM_TOPK:
        errs.append("semantic.top_k difiere")
    if a.get("semantic", {}).get("normalize") is not True:
        errs.append("semantic.normalize difiere")
    if a.get("semantic", {}).get("index") != "faiss.IndexFlatIP":
        errs.append("semantic.index difiere")
    if a.get("model") != SEM_MODEL:
        errs.append(f"model={a.get('model')}")
    if a.get("model_revision") != SEM_REVISION:
        errs.append(f"model_revision={a.get('model_revision')}")
    if a.get("normalization") != NORMALIZATION:
        errs.append(f"normalization={a.get('normalization')}")
    if a.get("fusion") != "(1-alpha)*lex_norm + alpha*sem_norm":
        errs.append("fusion difiere")
    if a.get("document_tie_break") != TIE_BREAK:
        errs.append(f"document_tie_break={a.get('document_tie_break')}")
    if errs:
        sys.exit("ERROR: alpha.json no coincide con la configuración congelada:\n  - " + "\n  - ".join(errs)
                 + "\nAvisa al humano; no se corrige aquí.")
    return a


# --------------------------------------------------------------------------------------
# Datos BEIR
# --------------------------------------------------------------------------------------
def load_beir(data_dir, ds, subset):
    data_dir = Path(data_dir)
    root = data_dir / ds
    if not (root / "corpus.jsonl").exists():
        zp = data_dir / f"{ds}.zip"
        data_dir.mkdir(parents=True, exist_ok=True)
        if not zp.exists():
            log(f"descargando {DATASET_URLS[ds]} (si falla: hazlo en el nodo de acceso)")
            urllib.request.urlretrieve(DATASET_URLS[ds], zp)
        with zipfile.ZipFile(zp) as z:
            z.extractall(data_dir)
    ids, texts, titles = [], [], []
    with open(root / "corpus.jsonl", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            ids.append(str(d["_id"]))
            title = d.get("title", "") or ""
            titles.append(title)
            texts.append(title + " " + (d.get("text", "") or ""))   # doc_text = title + ' ' + text
            if subset and len(ids) >= subset:
                break
    qtext = {}
    with open(root / "queries.jsonl", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            qtext[str(d["_id"])] = d["text"]

    def qids_from(split):
        p = root / "qrels" / f"{split}.tsv"
        if not p.exists():
            return []
        seen, out = set(), []
        with open(p, encoding="utf-8") as f:
            next(f, None)
            for line in f:
                q = line.split("\t")[0].strip()
                if q and q not in seen and q in qtext:
                    seen.add(q)
                    out.append(q)
        return out

    test_q = [(q, qtext[q]) for q in qids_from("test")]
    if ds == "fiqa":
        calib_q = [(q, qtext[q]) for q in qids_from("train")]
    else:  # trec-covid: títulos de 1.000 documentos al azar (seed 42)
        rng = np.random.default_rng(SEED)
        pool = [i for i, t in enumerate(titles) if t.strip()]
        pick = rng.choice(pool, size=min(1000, len(pool)), replace=False)
        calib_q = [(f"doc{ids[i]}", titles[i]) for i in pick]
    return ids, texts, calib_q, test_q


def fake_data(n_docs=1500, n_q=120):
    rng = np.random.default_rng(SEED)
    vocab = [f"palabra{i}" for i in range(400)] + ["the", "of", "and", "is", "running", "runs"]
    ids = [f"d{i}" for i in range(n_docs)]
    texts = [" ".join(rng.choice(vocab, size=int(rng.integers(20, 80)))) for _ in range(n_docs)]
    qs = [(f"q{i}", " ".join(rng.choice(vocab, size=int(rng.integers(3, 9))))) for i in range(n_q)]
    return ids, texts, qs[: n_q // 2], qs[n_q // 2:]


# --------------------------------------------------------------------------------------
# Backends (BM25, denso, reranker)
# --------------------------------------------------------------------------------------
class FakeDense:
    """Solo para probar la lógica sin modelos: embeddings por hash de tokens."""
    dim = 64

    def __init__(self):
        self._tok = {}
        self.lock = threading.Lock()

    def _vec(self, w):
        if w not in self._tok:
            r = np.random.default_rng(zlib.crc32(w.encode()))
            self._tok[w] = r.normal(size=self.dim)
        return self._tok[w]

    def embed(self, text):
        v = sum(self._vec(w) for w in text.lower().split()) if text.strip() else np.ones(self.dim)
        v = np.asarray(v, dtype=np.float32)
        return v / (np.linalg.norm(v) + 1e-9)

    def encode_corpus(self, texts, bs=64):
        return np.stack([self.embed(t) for t in texts]).astype(np.float32)

    def encode_query(self, q):
        time.sleep(0.004)
        return self.embed(q)


class RealDense:
    def __init__(self, device):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self.torch, self.device = torch, device
        self.tok = AutoTokenizer.from_pretrained(SEM_MODEL, revision=SEM_REVISION)
        self.model = AutoModel.from_pretrained(SEM_MODEL, revision=SEM_REVISION).to(device).eval()
        self.fp16 = device.startswith("cuda")
        if self.fp16:
            self.model = self.model.half()
        self.lock = threading.Lock()   # tokenizer Rust no es seguro con hilos concurrentes

    def _enc(self, texts):
        torch = self.torch
        b = self.tok(texts, padding=True, truncation=True, max_length=SEM_MAXLEN, return_tensors="pt").to(self.device)
        out = self.model(**b).last_hidden_state[:, 0]                  # pooling CLS
        out = torch.nn.functional.normalize(out.float(), p=2, dim=1)   # L2, float32
        return out.cpu().numpy().astype(np.float32)

    def encode_corpus(self, texts, bs=64):
        torch = self.torch
        order = np.argsort([-len(t) for t in texts])
        out = np.zeros((len(texts), self.model.config.hidden_size), dtype=np.float32)
        t0 = time.time()
        with torch.inference_mode():
            for bi, s in enumerate(range(0, len(texts), bs)):
                idx = order[s:s + bs]
                out[idx] = self._enc([texts[i] for i in idx])
                if bi % 50 == 0:
                    log(f"  embeddings {s}/{len(texts)} ({time.time() - t0:.0f}s)")
        return out

    def encode_query(self, q):
        with self.lock, self.torch.inference_mode():
            return self._enc([QUERY_PREFIX + q])[0]


class Backend:
    def __init__(self, ids, texts, args, fake):
        self.ids, self.texts, self.fake = ids, texts, fake
        order = np.argsort(np.array(ids, dtype=object), kind="stable")   # orden por ID string
        self.id_rank = np.empty(len(ids), dtype=np.int64)
        self.id_rank[order] = np.arange(len(ids))
        self.tl = threading.local()
        t0 = time.time()

        # ---- BM25 ----
        import bm25s
        import Stemmer
        self.bm25s = bm25s
        stemmer = Stemmer.Stemmer("english")
        log(f"fase 0: indexando BM25 ({len(ids)} docs)")
        tok = bm25s.tokenize(texts, stopwords="en", stemmer=stemmer, show_progress=False)
        self.bm = bm25s.BM25(method="lucene", k1=LEX["k1"], b=LEX["b"])
        self.bm.index(tok, show_progress=False)

        # ---- denso ----
        device = args.device
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"
        self.device = device
        if fake:
            self.dense = FakeDense()
        else:
            if device == "cpu":
                log("AVISO: sin GPU, se usa CPU en fp32 (solo para pruebas en laptop)")
            self.dense = RealDense(device)
        cache = Path(args.data_dir) / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        tag = "fake" if fake else ("fp16" if device.startswith("cuda") else "fp32")
        fingerprint = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()[:12]
        cpath = cache / f"emb_{args.dataset}_{len(ids)}_{fingerprint}_{SEM_REVISION[:8]}_{tag}.npy"
        if cpath.exists() and not args.no_cache and not fake:
            log(f"cargando embeddings de caché {cpath}")
            self.emb = np.load(cpath)
        else:
            log("calculando embeddings del corpus")
            self.emb = self.dense.encode_corpus(texts)
            if not fake and not args.no_cache:
                np.save(cpath, self.emb)
        import faiss
        try:
            faiss.omp_set_num_threads(1)
        except Exception:
            pass
        self.index = faiss.IndexFlatIP(self.emb.shape[1])
        self.index.add(self.emb)

        # ---- reranker: 2 réplicas en la misma GPU ----
        self.rr_locks = [threading.Lock(), threading.Lock()]
        if fake:
            self.rerankers = [None, None]
        else:
            from sentence_transformers import CrossEncoder
            self.rerankers = [CrossEncoder(RERANK_MODEL, max_length=RERANK_MAXLEN, device=device) for _ in range(2)]
        self.build_s = time.time() - t0
        log(f"fase 0: índices y modelos listos en {self.build_s:.0f}s")

    # ---- etapas (síncronas; se ejecutan en hilos) ----
    def _stemmer(self):
        if not hasattr(self.tl, "st"):
            import Stemmer
            self.tl.st = Stemmer.Stemmer("english")
        return self.tl.st

    def lex_search(self, q):
        toks = self.bm25s.tokenize(q, stopwords="en", stemmer=self._stemmer(), return_ids=False,
                                   show_progress=False)[0]
        full = np.asarray(self.bm.get_scores(toks), dtype=np.float64) if toks else np.zeros(len(self.ids))
        idx = topk_tiebreak(full, self.id_rank, LEX["top_k"])
        return SimpleNamespace(idx=idx, scores=full[idx], full=full)

    def sem_search(self, q):
        qv = self.dense.encode_query(q)
        k = min(20, len(self.ids))
        D, I = self.index.search(qv[None, :].astype(np.float32), k)
        D, I = D[0], I[0]
        order = np.lexsort((self.id_rank[I], -D))[:SEM_TOPK]
        return SimpleNamespace(idx=I[order], scores=D[order], qv=qv)

    def fuse(self, lres, sres, alpha):
        cand = np.unique(np.concatenate([lres.idx, sres.idx]))           # unión (<= 20)
        lex = lres.full[cand]                                              # completar puntajes léxicos
        sem = (self.emb[cand] @ sres.qv).astype(np.float64)               # completar puntajes semánticos
        f = (1.0 - alpha) * minmax(lex) + alpha * minmax(sem)
        order = np.lexsort((self.id_rank[cand], -f))
        return cand[order], f[order]

    def rerank(self, replica, q, cand):
        if self.fake:
            with self.rr_locks[replica]:
                time.sleep(0.012 + 0.004 * len(cand) / 20)
                rng = np.random.default_rng(zlib.crc32((q + str(replica)).encode()))
                return rng.random(len(cand))
        pairs = [(q, self.texts[i]) for i in cand]
        with self.rr_locks[replica]:
            s = self.rerankers[replica].predict(pairs, batch_size=len(pairs), show_progress_bar=False,
                                                convert_to_numpy=True)
        return np.asarray(s, dtype=np.float64).reshape(-1)


# --------------------------------------------------------------------------------------
# Servicio asíncrono + generador de carga
# --------------------------------------------------------------------------------------
class Service:
    def __init__(self, be, alpha, dataset, threads):
        self.be, self.alpha, self.dataset = be, alpha, dataset
        mk = lambda n: cf.ThreadPoolExecutor(max_workers=n)
        self.threads = threads
        self._init_pools()
        self.cond = Cond(name="-", load=0, hedging=False, rerank=True, faults={})
        self.thr = 1e9            # umbral de hedging (s); se fija tras calibrar
        self.orig_t = collections.deque()
        self.copy_t = collections.deque()
        self.measurement_warmup = None
        self.post_orig = 0
        self.post_copies = 0

    def _init_pools(self):
        # Pools propios de cada tramo para que ningún hilo residual contamine
        # la siguiente condición o escalón de carga.
        mk = lambda n: cf.ThreadPoolExecutor(max_workers=n)
        self.pool_lex, self.pool_sem = mk(self.threads), mk(self.threads)
        self.pool_rr, self.pool_fuse = mk(self.threads), mk(2)

    async def quiesce(self):
        # asyncio cancela futures pero NO interrumpe inferencias de PyTorch en
        # hilos ya iniciados. Esperamos a que terminen fuera de la ventana de
        # medición, descartamos las tareas aún en cola y renovamos los pools.
        pools = (self.pool_lex, self.pool_sem, self.pool_rr, self.pool_fuse)
        await asyncio.gather(*(asyncio.to_thread(
            pool.shutdown, wait=True, cancel_futures=True) for pool in pools))
        self._init_pools()

    def set_condition(self, cond, thr_s):
        self.cond, self.thr = cond, thr_s
        self.orig_t.clear()
        self.copy_t.clear()
        self.post_orig = 0
        self.post_copies = 0

    # ---- hedging: presupuesto de copias (máx. 10 % de las originales en 60 s) ----
    def hedge_allowed(self, now, in_measurement):
        for dq in (self.orig_t, self.copy_t):
            while dq and now - dq[0] > HEDGE_WINDOW_S:
                dq.popleft()
        # Comprobar el efecto de AÑADIR una copia, no solamente el estado actual.
        rolling_ok = (len(self.copy_t) + 1) <= HEDGE_MAX_EXTRA * len(self.orig_t) + 1e-9
        # El summary.csv descarta el calentamiento; usar idéntico denominador
        # para que el porcentaje reportado tampoco supere 10 %.
        post_ok = (not in_measurement or
                   (self.post_copies + 1) <= HEDGE_MAX_EXTRA * self.post_orig + 1e-9)
        return rolling_ok and post_ok

    async def _body(self, key, fn, pool, rec, u):
        await apply_fault(self.cond.faults.get(key, "ok"), u.get(key, 1.0), rec)
        return await asyncio.get_running_loop().run_in_executor(pool, fn)

    async def timed(self, name, fn, pool, timeout_s, rec, u):
        t = time.perf_counter()
        ok, val = False, None
        try:
            val = await asyncio.wait_for(self._body(name, fn, pool, rec, u), timeout_s)
            ok = True
        except asyncio.TimeoutError:
            rec["timeouts"].append(name)
        except Exception as e:  # noqa: BLE001
            rec["errors"].append(f"{name}:{type(e).__name__}")
        rec["stage_ms"][name] = (time.perf_counter() - t) * 1000.0
        return ok, val

    async def _rr_call(self, key, replica, q, cand, rec, u):
        await apply_fault(self.cond.faults.get(key, "ok"), u.get(key, 1.0), rec)
        return await asyncio.get_running_loop().run_in_executor(
            self.pool_rr, functools.partial(self.be.rerank, replica, q, cand))

    async def rerank_hedged(self, rec, q, cand, u):
        """Réplica A; si no responde antes del umbral (o falla) y hay presupuesto, copia a B.
        Gana la primera respuesta válida dentro de 1,2 s desde el envío a A. Si una réplica
        falla y la otra sigue en curso, se espera a la otra hasta el plazo."""
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        deadline = t0 + RERANK_TO
        self.orig_t.append(t0)
        in_measurement = (self.measurement_warmup is not None and
                          rec["t_sched"] >= self.measurement_warmup)
        if in_measurement:
            self.post_orig += 1
        tasks = {}

        def launch(key, replica, tag):
            tk = asyncio.ensure_future(self._rr_call(key, replica, q, cand, rec, u))
            tasks[tk] = tag
            return tk

        pending = {launch("rerank_a", 0, "a")}
        decided = not self.cond.hedging
        result = None
        while pending and result is None:
            now = loop.time()
            remaining = deadline - now
            if remaining <= 0:
                break
            wait_t = remaining if decided else min(remaining, max(0.0, t0 + self.thr - now))
            done, pending = await asyncio.wait(pending, timeout=wait_t, return_when=asyncio.FIRST_COMPLETED)
            failed_now = False
            for d in done:
                exc = d.exception()
                if exc is None:
                    if result is None:
                        result = (d.result(), tasks[d])
                else:
                    rec["errors"].append(f"rerank_{tasks[d]}:{type(exc).__name__}")
                    failed_now = True
            if result is not None:
                break
            if not decided and (failed_now or not done):
                decided = True
                now = loop.time()
                if now < deadline and self.hedge_allowed(now, in_measurement):
                    rec["hedge_sent"] = True
                    self.copy_t.append(now)
                    if in_measurement:
                        self.post_copies += 1
                    pending.add(launch("rerank_b", 1, "b"))
        for p in pending:
            p.cancel()
        end = loop.time()
        rec["stage_ms"]["rerank"] = (end - t0) * 1000.0
        if result is None:
            if end >= deadline - 0.002:
                rec["timeouts"].append("rerank")
            return None
        rec["hedge_won"] = result[1] == "b"
        return result[0]

    async def handle(self, rec, q, u, t_origin):
        be, loop = self.be, asyncio.get_running_loop()
        try:
            (lok, lres), (sok, sres) = await asyncio.gather(
                self.timed("lex", functools.partial(be.lex_search, q), self.pool_lex, LEX_TO, rec, u),
                self.timed("sem", functools.partial(be.sem_search, q), self.pool_sem, SEM_TO, rec, u))
            idxs, route = [], "error"
            if lok and sok:
                fok, fres = await self.timed("fusion", functools.partial(be.fuse, lres, sres, self.alpha),
                                             self.pool_fuse, FUS_TO, rec, u)
                if fok:
                    cand, _ = fres
                    if self.cond.rerank:
                        rec["rerank_invoked"] = True
                        scores = await self.rerank_hedged(rec, q, cand, u)
                        if scores is not None:
                            order = np.lexsort((be.id_rank[cand], -scores))
                            idxs, route = cand[order][:3], "reranked"
                        else:
                            idxs, route = cand[:3], "fused_fallback"
                    else:
                        idxs, route = cand[:3], "fused_baseline"      # línea base: reranker NO se invoca
                else:
                    idxs, route = sres.idx[:3], "sem"                  # (la fusión falló: se usa lo semántico)
            elif lok:
                idxs, route = lres.idx[:3], "lex"
            elif sok:
                idxs, route = sres.idx[:3], "sem"
            rec["route"] = route
            rec["doc_ids"] = [be.ids[i] for i in idxs]
            rec["n_results"] = len(rec["doc_ids"])
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            rec["route"], rec["doc_ids"], rec["n_results"] = "error", [], 0
            rec["errors"].append(f"internal:{type(e).__name__}:{e}")
        rec["t_end"] = loop.time() - t_origin
        rec["latency_ms"] = (rec["t_end"] - rec["t_sched"]) * 1000.0   # desde la hora PROGRAMADA

    async def run_load(self, qps, queries, rep, cond_name, duration=None, n=None, arrival_key=None, drain_s=10.0):
        """Open-loop: cada solicitud se lanza en su hora programada sin esperar a las anteriores."""
        loop = asyncio.get_running_loop()
        rng = np.random.default_rng([SEED, rep] + ([arrival_key] if arrival_key is not None else []))
        times = poisson_arrivals(qps, rng, duration=duration, n=n)
        t_origin = loop.time() + 0.05
        recs, tasks = [], []
        for i, ts in enumerate(times):
            wait = t_origin + ts - loop.time()
            if wait > 0:
                await asyncio.sleep(wait)
            qid, qtext = queries[i % len(queries)]
            rec = {"dataset": self.dataset, "rep": rep, "condition": cond_name, "qid": str(qid),
                   "t_sched": ts, "t_end": None, "latency_ms": None, "route": None, "n_results": 0,
                   "timeouts": [], "errors": [], "rerank_invoked": False, "delay_injected": False,
                   "hedge_sent": False, "hedge_won": False,
                   "stage_ms": {"lex": 0.0, "sem": 0.0, "fusion": 0.0, "rerank": 0.0}, "doc_ids": []}
            recs.append(rec)
            tasks.append(asyncio.create_task(self.handle(rec, qtext, draws(rep, i), t_origin)))
        if tasks:
            _, pend = await asyncio.wait(tasks, timeout=drain_s)
            for p in pend:
                p.cancel()
            if pend:
                await asyncio.gather(*pend, return_exceptions=True)
        now = loop.time() - t_origin
        for rec in recs:                       # lo que no terminó cuenta como fallo (no se esconde la cola)
            if rec["latency_ms"] is None:
                rec["route"], rec["n_results"], rec["doc_ids"] = "error", 0, []
                rec["errors"].append("unfinished")
                rec["t_end"] = now
                rec["latency_ms"] = (now - rec["t_sched"]) * 1000.0
        return recs


# --------------------------------------------------------------------------------------
# Resúmenes
# --------------------------------------------------------------------------------------
def write_jsonl(path, recs):
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            r = dict(r)
            r["t_sched"] = round(r["t_sched"], 4)
            r["t_end"] = round(r["t_end"], 4)
            r["latency_ms"] = round(r["latency_ms"], 3)
            r["stage_ms"] = {k: round(v, 3) for k, v in r["stage_ms"].items()}
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")


SUMMARY_FIELDS = (["dataset", "rep", "condition", "offered_qps", "offered_qps_measured", "achieved_qps",
                   "n_sent", "p50_ms", "p95_ms", "p99_ms", "rerank_p99_ms", "pct_errors",
                   "pct_timeout_lex", "pct_timeout_sem", "pct_timeout_fusion", "pct_timeout_rerank",
                   "continuity_pct", "pct_dup"] + [f"pct_route_{r}" for r in ROUTES])


def summarize(recs, dataset, rep, cond, offered_qps, warmup, duration):
    post = [r for r in recs if r["t_sched"] >= warmup]      # se descartan los primeros 30 s
    n = len(post)
    win = max(duration - warmup, 1e-9)
    valid = [r for r in post if r["n_results"] == 3]
    lat = [r["latency_ms"] for r in valid]
    pct = lambda c: 100.0 * c / n if n else float("nan")
    rr_valid = [r["stage_ms"]["rerank"] for r in valid if r["rerank_invoked"] and r["route"] == "reranked"]
    originals = sum(1 for r in post if r["rerank_invoked"])
    row = {"dataset": dataset, "rep": rep, "condition": cond, "offered_qps": round(offered_qps, 4),
           "offered_qps_measured": round(n / win, 4), "achieved_qps": round(len(valid) / win, 4), "n_sent": n,
           "p50_ms": pctl(lat, 50), "p95_ms": pctl(lat, 95), "p99_ms": pctl(lat, 99),
           "rerank_p99_ms": pctl(rr_valid, 99),
           "pct_errors": pct(sum(1 for r in post if r["route"] == "error"))}
    for st in STAGES:
        row[f"pct_timeout_{st}"] = pct(sum(1 for r in post if st in r["timeouts"]))
    row["continuity_pct"] = pct(sum(1 for r in post if r["n_results"] == 3 and r["latency_ms"] <= SLO_MS))
    row["pct_dup"] = 100.0 * sum(1 for r in post if r["hedge_sent"]) / originals if originals else 0.0
    for rt in ROUTES:
        row[f"pct_route_{rt}"] = pct(sum(1 for r in post if r["route"] == rt))
    return row


def append_summary(path, row):
    new = not Path(path).exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()})


# --------------------------------------------------------------------------------------
# run_meta.json
# --------------------------------------------------------------------------------------
def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except Exception as e:  # noqa: BLE001
        return f"no disponible: {e}"


def write_meta(path, args, alpha, calib, extra=None):
    libs = {}
    for lib in ["torch", "transformers", "sentence-transformers", "faiss-cpu", "bm25s", "PyStemmer", "numpy"]:
        try:
            libs[lib] = md.version(lib)
        except Exception:  # noqa: BLE001
            libs[lib] = None
    meta = {"node": socket.gethostname(), "slurm_nodename": os.environ.get("SLURMD_NODENAME"),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "nvidia_smi": sh(["nvidia-smi"]), "lscpu": sh(["lscpu"]),
            "python": sys.version, "platform": platform.platform(), "libraries": libs,
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "frozen_config": FROZEN_CONFIG, "args": vars(args), "alpha_json": alpha, "calibration_json": calib}
    if extra:
        meta.update(extra)
    json.dump(meta, open(path, "w"), indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------------------
# Calibración y repeticiones
# --------------------------------------------------------------------------------------
async def calibrate(svc, calib_q, args, out):
    cond = Cond(name="CALIB", load=0, hedging=False, rerank=True, faults={})
    svc.set_condition(cond, 1e9)
    svc.measurement_warmup = None
    log(f"calibración (a): {args.calib_queries} consultas a 1 QPS")
    recs = await svc.run_load(1.0, calib_q, 0, "CALIB", n=args.calib_queries, arrival_key=1)
    await svc.quiesce()
    ok = [r for r in recs if r["route"] == "reranked"]
    stage = {}
    for st in STAGES:
        v = [r["stage_ms"][st] for r in ok]
        stage[st] = {"p50": pctl(v, 50), "p95": pctl(v, 95), "p99": pctl(v, 99), "n": len(v)}
    e2e = [r["latency_ms"] for r in recs if r["n_results"] == 3]
    stage["end_to_end"] = {"p50": pctl(e2e, 50), "p95": pctl(e2e, 95), "p99": pctl(e2e, 99), "n": len(e2e)}
    thr_ms = stage["rerank"]["p95"]
    log(f"  umbral de hedging = p95 reranker = {thr_ms:.1f} ms | e2e p99 = {stage['end_to_end']['p99']:.1f} ms")
    write_jsonl(Path(out) / f"requests_{args.dataset}_calib_1qps.jsonl", recs)

    log("calibración (b): rampa")
    svc.set_condition(Cond(name="RAMP", load=0, hedging=True, rerank=True, faults={}), thr_ms / 1000.0)
    ramp, C, C_hybrid, C_any = [], 0.0, 0.0, 0.0
    first_failure = False
    for k, qps in enumerate(args.rates):
        recs = await svc.run_load(float(qps), calib_q, 0, f"RAMP{qps}", duration=args.ramp_seconds, arrival_key=100 + k)
        await svc.quiesce()
        n = len(recs)
        valid = [r for r in recs if r["n_results"] == 3]
        hybrid = [r for r in recs if r["route"] == "reranked" and r["n_results"] == 3]
        half = args.ramp_seconds / 2.0
        p99a = pctl([r["latency_ms"] for r in valid if r["t_sched"] < half], 99)
        p99b = pctl([r["latency_ms"] for r in valid if r["t_sched"] >= half], 99)
        achieved_qps = len(valid) / args.ramp_seconds
        hybrid_qps = len(hybrid) / args.ramp_seconds
        # Medir la tasa real de llegadas Poisson y el rendimiento de cada ruta.
        # En una ventana Poisson, la tasa REALMENTE ofrecida es n / duration,
        # no exactamente el parámetro nominal qps. Comparar contra las llegadas
        # efectivas evita confundir ruido del generador con incapacidad del servidor.
        actual_offered_qps = n / args.ramp_seconds
        # Diagnóstico del servicio con respaldo (metodología v3).
        throughput_any = bool(n and achieved_qps >= 0.99 * actual_offered_qps)
        stable_any = (p99b <= 1.2 * p99a) if not (math.isnan(p99a) or math.isnan(p99b)) else False
        passes_any = bool(throughput_any and stable_any)

        # Metodología v4: capacidad de la ruta COMPLETA, sin contar respaldos.
        # El percentil se obtiene solo de las consultas que llegaron a `reranked`.
        hp99a = pctl([r["latency_ms"] for r in hybrid if r["t_sched"] < half], 99)
        hp99b = pctl([r["latency_ms"] for r in hybrid if r["t_sched"] >= half], 99)
        hybrid_fraction = len(hybrid) / n if n else 0.0
        throughput_ok = bool(n and hybrid_qps >= 0.99 * actual_offered_qps)
        stable = (hp99b <= 1.2 * hp99a) if not (math.isnan(hp99a) or math.isnan(hp99b)) else False
        passes = bool(throughput_ok and stable)
        passes_hybrid = passes  # compatibilidad con los reportes v3
        step = {
            "offered_qps": qps, "offered_qps_measured": actual_offered_qps,
            "n_sent": n, "achieved_qps": achieved_qps,
            "throughput_ratio": achieved_qps / actual_offered_qps if n else 0.0,
            "throughput_ratio_vs_nominal": achieved_qps / float(qps),
            "delivered_fraction": len(valid) / n if n else 0.0,
            "hybrid_qps": hybrid_qps,
            "hybrid_fraction": hybrid_fraction,
            "p99_first_half_ms": p99a, "p99_second_half_ms": p99b,
            "p99_stable": bool(stable), "passes": passes,
            "passes_hybrid_diagnostic": passes_hybrid,
            "passes_any_route_diagnostic": passes_any,
            "p99_any_route_stable": bool(stable_any),
            "hybrid_p99_first_half_ms": hp99a,
            "hybrid_p99_second_half_ms": hp99b,
            "pct_reranked": 100.0 * hybrid_fraction,
        }
        ramp.append(step)
        if passes_any:
            C_any = max(C_any, float(qps))
        if passes_hybrid:
            C_hybrid = max(C_hybrid, float(qps))
        # Primera falla como frontera: seguimos registrando el resto de la rampa,
        # pero no aumentamos C después de esa primera falla.
        if not passes:
            first_failure = True
        if passes and not first_failure:
            C = max(C, float(qps))
        log(f"  {qps:>3} QPS: logrado {achieved_qps:.2f} | "
            f"p99 {p99a:.0f}->{p99b:.0f} ms | reranked {100*hybrid_fraction:.0f}% | "
            f"ruta completa {'OK' if passes else 'NO'} | "
            f"cualquier ruta {'OK' if passes_any else 'NO'}")
        # Evaluar toda la rampa definida: un escalón puede fallar por variación
        # estocástica y recuperarse en el siguiente; registrar esa variación.
        await asyncio.sleep(3)
        gc.collect()
    if C <= 0:
        sys.exit("ERROR: el primer escalón no sostuvo >=99% de consultas reranked con p99 estable; "
                 "no se puede fijar C con este criterio; revisa la rampa y repite la calibración.")
    calib = {"C_qps": C, "C_any_route_diagnostic": C_any,
             "C_hybrid_qps_diagnostic": C_hybrid,
             "hybrid_diagnostic_rule": "ruta reranked en >=99% de solicitudes, p99 estable; "
                                       "C_qps se detiene en el primer escalón fallido",
             "hedge_threshold_ms": thr_ms, "stage_percentiles_1qps_ms": stage,
             "ramp": ramp, "ramp_seconds": args.ramp_seconds,
             "n_calib_queries": args.calib_queries,
             "note": "V4 experimental: C_qps requiere ruta completa reranked y p99 estable; "
                     "C_any_route_diagnostic conserva la capacidad de cualquier ruta (v3)"}
    json.dump(calib, open(Path(out) / "calibration.json", "w"), indent=2)
    log(f"C ruta completa (hasta primera falla) = {C} QPS | "
        f"C cualquier ruta (diagnóstico) = {C_any} QPS | "
        f"C híbrido sin corte (diagnóstico) = {C_hybrid} QPS | "
        f"umbral hedging = {thr_ms:.1f} ms")
    return calib


async def run_reps(svc, test_q, calib, conds, args, out):
    C, thr_s = calib["C_qps"], calib["hedge_threshold_ms"] / 1000.0
    for rep in range(1, args.reps + 1):
        for cond in conds:
            path = Path(out) / f"requests_{args.dataset}_rep{rep}_{cond.name}.jsonl"
            if args.resume and path.exists():
                log(f"rep{rep} {cond.name}: ya existe, se salta (--resume)")
                continue
            qps = cond.load * C
            svc.set_condition(cond, thr_s)
            svc.measurement_warmup = args.warmup_seconds
            log(f"rep{rep} {cond.name}: {qps:.2f} QPS durante {args.cond_seconds}s")
            recs = await svc.run_load(qps, test_q, rep, cond.name, duration=args.cond_seconds)
            await svc.quiesce()
            write_jsonl(path, recs)
            row = summarize(recs, args.dataset, rep, cond.name, qps, args.warmup_seconds, args.cond_seconds)
            append_summary(Path(out) / "summary.csv", row)
            log(f"  n={row['n_sent']} p99={row['p99_ms']:.0f}ms cont={row['continuity_pct']:.1f}% "
                f"dup={row['pct_dup']:.1f}% rutas=" +
                ",".join(f"{r}:{row['pct_route_' + r]:.0f}" for r in ROUTES if row['pct_route_' + r] > 0))
            await asyncio.sleep(2)
            gc.collect()


async def amain(args, be, alpha, calib_q, test_q, out):
    svc = Service(be, alpha["alpha"], args.dataset, args.threads)
    calib = None
    cpath = Path(out) / "calibration.json"
    if args.phase in ("all", "calib"):
        if args.reuse_calibration and cpath.exists():
            calib = json.load(open(cpath))
            log(f"se reutiliza {cpath}")
        else:
            calib = await calibrate(svc, calib_q, args, out)
        write_meta(Path(out) / "run_meta.json", args, alpha, calib, {"phase0_seconds": be.build_s})
    if args.phase in ("all", "runs"):
        if calib is None:
            if not cpath.exists():
                sys.exit("ERROR: falta calibration.json; corre primero --phase calib")
            calib = json.load(open(cpath))
        allc = make_conditions()
        names = [c.name for c in allc] if args.conditions == "all" else args.conditions.split(",")
        conds = [c for c in allc if c.name in names]
        missing = set(names) - {c.name for c in conds}
        if missing:
            sys.exit(f"ERROR: condiciones desconocidas: {sorted(missing)}")
        await run_reps(svc, test_q, calib, conds, args, out)
        write_meta(Path(out) / "run_meta.json", args, alpha, calib, {"phase0_seconds": be.build_s})
    log("listo. Copia results/ fuera de Khipu (scp/rsync): no hay backup.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["fiqa", "trec-covid"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", default="results")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--alpha-json", default="alpha.json")
    ap.add_argument("--subset", type=int, default=0, help="usar solo los primeros N documentos (pruebas)")
    ap.add_argument("--cond-seconds", type=float, default=180.0)
    ap.add_argument("--warmup-seconds", type=float, default=30.0)
    ap.add_argument("--calib-queries", type=int, default=500)
    ap.add_argument("--ramp-seconds", type=float, default=120.0)
    ap.add_argument("--ramp-rates", default="1,2,4,8,16,32,64")
    ap.add_argument("--quick", action="store_true", help="piloto: 60 s por condición, 1 repetición, rampa corta")
    ap.add_argument("--fake", action="store_true", help="datos y modelos sintéticos (solo probar la lógica)")
    ap.add_argument("--phase", default="all", choices=["all", "calib", "runs"])
    ap.add_argument("--conditions", default="all", help="lista separada por comas, p. ej. L100,F1,F3H")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--reuse-calibration", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()
    args.rates = [float(x) for x in args.ramp_rates.split(",")]
    if args.quick:
        args.calib_queries, args.ramp_seconds = 50, 15.0
        args.cond_seconds, args.warmup_seconds, args.reps = 60.0, 10.0, 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    alpha = load_and_check_alpha(args.alpha_json)        # se detiene si algo difiere
    write_meta(out / "run_meta.json", args, alpha, None)  # copia alpha.json dentro de run_meta.json

    if args.fake:
        ids, texts, calib_q, test_q = fake_data()
    else:
        ids, texts, calib_q, test_q = load_beir(args.data_dir, args.dataset, args.subset)
    log(f"{args.dataset}: {len(ids)} docs | calib {len(calib_q)} consultas | test {len(test_q)} consultas")
    if not args.fake:
        try:
            import torch
            torch.manual_seed(SEED)
        except Exception:  # noqa: BLE001
            pass
    if not args.fake and os.environ.get("SLURM_JOB_ID"):
        import torch
        if not torch.cuda.is_available():
            sys.exit("ERROR: no se detecta CUDA dentro del job Slurm")
    be = Backend(ids, texts, args, args.fake)
    # calentamiento: 50 consultas (sin registrar)
    for i in range(50):
        q = calib_q[i % len(calib_q)][1]
        lr, sr = be.lex_search(q), be.sem_search(q)
        cand, _ = be.fuse(lr, sr, alpha["alpha"])
        be.rerank(0, q, cand)
        be.rerank(1, q, cand)
    log("calentamiento listo")
    asyncio.run(amain(args, be, alpha, calib_q, test_q, out))


if __name__ == "__main__":
    main()
