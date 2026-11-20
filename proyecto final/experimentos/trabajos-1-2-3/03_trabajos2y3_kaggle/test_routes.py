"""Quick logic check: every fault condition reaches the expected route (Table 2)."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from minion_bench import (CONFIG, CONDITIONS, Engine, Service, build_query_sets, load_alpha, load_dataset)


async def run():
    alpha = load_alpha("alpha.json")["alpha"]
    corpus, queries, train_q, test_q = load_dataset("fiqa", ".smoke/data")
    corpus = corpus[:300]
    calib_q, test = build_query_sets("fiqa", corpus, queries, train_q, test_q)
    engine = Engine(corpus, alpha, "cpu", 16)
    service = Service(engine)
    service.threshold_s = 2.0  # fake threshold just to exercise the hedge path

    cases = {  # condition -> expected route (one request each)
        "normal": ({"lex": "ok"}, True, True, "reranked"),
        "norerank": ({}, False, False, "fused_baseline"),
        "F1": ({"rerank_a": "error", "rerank_b": "error"}, True, True, "fused_fallback"),
        "F2": ({"rerank_a": "delay:5000", "rerank_b": "delay:5000"}, True, True, "fused_fallback"),
        "F4": ({"sem": "error"}, True, True, "lex"),
        "F5": ({"lex": "error"}, True, True, "sem"),
        "F6": ({"lex": "error", "sem": "error"}, True, True, "error"),
        "F1_nobudget": ({"rerank_a": "error", "rerank_b": "delay:9999"}, True, True, "fused_fallback"),
    }
    for name, (faults, hedging, rerank, expected) in cases.items():
        ctx = {"dataset": "fiqa", "condition": name, "rep": 1, "faults": faults, "hedging": hedging,
               "rerank": rerank, "t0": 0.0}
        import time
        ctx["t0"] = time.perf_counter() - 0.001
        r = await service.handle(ctx, 7, "q-test", "what is the stock market?", ctx["t0"])
        ok = "OK " if r["route"] == expected else "FAIL"
        print(f"{ok} {name:14s} route={r['route']:15s} expected={expected:15s} lat={r['latency_ms']:8.1f}ms "
              f"timeouts={r['timeouts']} errors={r['errors']} hedge={r['hedge_sent']}")

    # delay_prob determinism: same rep+index must give same draws
    import numpy as np
    a = np.random.default_rng([42, 1, 5]).random(4)
    b = np.random.default_rng([42, 1, 5]).random(4)
    print("determinism:", "OK" if np.allclose(a, b) else "FAIL", a)

    # hedge budget: F3H-style delay_prob -> replicas a slow 5%; check hedge sends counted
    ctx = {"dataset": "fiqa", "condition": "F3H", "rep": 1, "faults": {"rerank_a": "delay_prob:1.0:100"},
           "hedging": True, "rerank": True, "t0": 0.0}
    import time
    sent = 0
    for i in range(3):
        ctx["t0"] = time.perf_counter() - 0.001
        r = await service.handle(ctx, i, "q", "what is the stock market?", ctx["t0"])
        sent += r["hedge_sent"]
    print("hedge sends with 100% slow replica a (should be >0):", sent)


asyncio.run(run())
