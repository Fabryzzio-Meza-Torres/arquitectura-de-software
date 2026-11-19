"""Prueba rápida (1-3 min) de que un modelo sirve ANTES de gastar horas de GPU.

Para cada modelo: carga, comprueba que los dígitos 0-4 son un token cada uno, puntúa un par obviamente relevante y otro
obviamente irrelevante (RG-S), genera un one-pager de prueba, y prueba un batch de 10 prompts largos (memoria).
Escribe un JSON con los modelos que pasaron y por qué fallaron los demás; sale con error si no pasó ninguno.

  python calidad/src/verificar_modelo.py --modelos Qwen/Qwen2.5-3B-Instruct Qwen/Qwen2.5-1.5B-Instruct --out modelos_ok.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_semantico as llm  # noqa: E402
from generar_onepagers import generar, limpiar, prompt_para  # noqa: E402
from io_formats import force_utf8_output  # noqa: E402

CONSULTA = "How do I reduce the taxes I pay on stock dividends?"
SI = "Qualified dividends are taxed at lower capital gains rates, and holding stocks in a retirement account such as an IRA defers or avoids dividend taxes."
NO = "The recipe calls for two cups of flour, three eggs and a pinch of salt; bake the cake for forty minutes."
LARGO = ("Stocks, bonds and funds pay interest and dividends that are reported every year. " * 60)[:3800]


def probar(modelo: str, device: str) -> dict:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    t0 = time.perf_counter()
    r = {"modelo": modelo, "ok": False}
    try:
        sc = llm.Rgs(modelo, device)  # falla si los dígitos 0-4 no son un token cada uno
        (p_si, m_si), (p_no, m_no) = sc.probs([llm.PROMPT_RGS.format(query=CONSULTA, doc=SI),
                                                llm.PROMPT_RGS.format(query=CONSULTA, doc=NO)])
        e_si, e_no = llm.esperanza(p_si), llm.esperanza(p_no)
        r.update({"score_relevante": round(e_si, 3), "score_irrelevante": round(e_no, 3),
                  "masa_digitos": [round(m_si, 3), round(m_no, 3)]})
        if not all(math.isfinite(x) for x in (m_si, m_no, e_si, e_no)):
            raise RuntimeError("el modelo produce valores inválidos (NaN/inf) en esta GPU; prueba otro modelo")
        if min(m_si, m_no) < llm.MASA_MINIMA:
            raise RuntimeError(f"el modelo no responde con un dígito 0-4 (masa {m_si:.2f}/{m_no:.2f})")
        if e_si <= e_no:
            raise RuntimeError(f"no distingue lo obvio: relevante {e_si:.2f} <= irrelevante {e_no:.2f}")
        sc.probs([llm.PROMPT_RGS.format(query=CONSULTA, doc=LARGO)] * 10)  # batch de 10 con documentos largos
        enc = sc.tok([sc._texto(prompt_para({"title": "Dividends", "text": SI * 3}, 90))], return_tensors="pt",
                     padding=True).to(device)
        txt = limpiar(generar(sc.model, sc.tok, enc, 160, torch)[0])
        r["onepager_ejemplo"] = txt
        if len(txt.split()) < 5:
            raise RuntimeError("no generó un one-pager")
        if device.startswith("cuda"):
            r["vram_pico_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)
        r["ok"] = True
    except Exception as e:  # noqa: BLE001
        r["error"] = f"{type(e).__name__}: {e}"
    r["segundos"] = round(time.perf_counter() - t0, 1)
    return r


def main() -> None:
    force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelos", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    res = []
    for m in args.modelos:
        r = probar(m, args.device)
        print(json.dumps(r, ensure_ascii=False, indent=1), file=sys.stderr)
        res.append(r)
        try:  # libera la GPU antes del siguiente modelo
            import gc, torch
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
        except Exception:  # noqa: BLE001
            pass
    Path(args.out).write_text(json.dumps({"ok": [r["modelo"] for r in res if r["ok"]], "detalle": res},
                                         ensure_ascii=False, indent=1), encoding="utf-8")
    if not any(r["ok"] for r in res):
        raise SystemExit("Ningún modelo pasó la verificación. Revisa el detalle en " + args.out)


if __name__ == "__main__":
    main()