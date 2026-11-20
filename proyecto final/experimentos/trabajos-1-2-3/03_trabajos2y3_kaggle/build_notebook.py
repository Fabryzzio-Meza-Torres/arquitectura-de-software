"""Build and execute trabajo{2|3}_latencia_{ds}.ipynb from the downloaded results."""
import argparse
import json
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

INFO = {"fiqa": (2, "FiQA-2018"), "trec-covid": (3, "TREC-COVID")}


def md(s):
    return nbf.v4.new_markdown_cell(s)


def code(s):
    return nbf.v4.new_code_cell(s)


def build(ds, root, figs, out):
    n, name = INFO[ds]
    c = []
    c += [md(f"# Trabajo {n} - Latencia y fallas de MINION en {name}\n\n"
             "Paper: *MINION: Parallel Hybrid Retrieval and Reranking under a Latency Budget*. "
             "Todos los numeros de este cuaderno se calculan a partir de los archivos de `results/`; "
             "ningun valor esta escrito a mano en el texto."),
          md("## 1. Objetivo\n\nResponder la parte de latencia y continuidad del paper: (i) p99 de extremo a extremo "
             "<= SLO bajo carga hasta 100 % de la capacidad C; (iii) continuidad >= 99 % cuando el reranker falla o se "
             "demora (rutas de la Tabla 2); (iv) solicitudes duplicadas (hedging) <= 10 %. La calidad (P@3, fitness ii) "
             "se calcula en el Trabajo 1."),
          code("import sys, json\nfrom IPython.display import Markdown, display\nimport pandas as pd\n"
               f"sys.path.insert(0, '.')\nfrom analysis_lib import Run\n"
               f"R = Run({ds!r}, root={str(root)!r}, figs={str(figs)!r})\npd.set_option('display.width', 200)\n"
               "pd.set_option('display.max_columns', 50)"),
          md("## 2. Montaje\n\nHardware y versiones leidos de `run_meta.json`."),
          code("hw = R.hardware()\nfor k, v in hw.items():\n    print(f'{k}: {v}')"),
          md("Arquitectura (se imprime desde la configuracion congelada guardada en `run_meta.json`):"),
          code("cfg = R.meta['config']; to = cfg['timeouts_ms']\nprint(f\"\"\"\n"
               "generador de carga (Poisson, open-loop, semilla {cfg['seed']})\n"
               "  consulta(q):\n"
               "    lex, sem = gather(wait_for(bm25s, {to['lexical']} ms), wait_for({cfg['semantic']['model']}, {to['semantic']} ms))\n"
               "    candidatos = union (<= 2 x {cfg['lexical']['top_k']}) -> min-max por consulta -> fusion alpha={R.meta['alpha_json']['alpha']} (wait_for {to['fusion']} ms)\n"
               "    top3 = rerank_con_hedging({cfg['reranker']['model']}, {cfg['reranker']['replicas']} replicas, plazo {to['rerank']} ms)\n"
               "    ruta segun la Tabla 2 (SLO {cfg['slo_ms']} ms)\n\"\"\")"),
          md("Condiciones: `L25-L100` = sistema completo con hedging sin fallas al 25/50/75/100 % de C; `NORERANK` = "
             "linea base que no invoca el reranker; `NOHEDGE` = 100 % de C sin hedging; `F1`/`F2` = reranker con error o "
             "con demora de 1500 ms en ambas replicas; `F3H`/`F3NH` = demora de 800 ms con p=0.05 en la replica A, con y "
             "sin hedging, con llegadas y demoras identicas; `F4`/`F5`/`F6` = fallas de la busqueda semantica, lexica o "
             "ambas."),
          code("pd.DataFrame(R.meta['settings'].items(), columns=['setting', 'value'])"),
          md("## 3. Calibracion\n\nK1: rampa de carga (C = mayor tasa con throughput >= 99 % de lo enviado y p99 "
             "estable). K2: latencia por etapa a 1 QPS."),
          code("R.k1()"),
          code("R.ramp_table()"),
          code("R.k2()"),
          code("R.stage_table()"),
          code("display(Markdown(f\"**C = {R.C} QPS**; umbral de hedging = p95 del reranker = \"\n"
               "                 f\"**{R.cal['hedge_threshold_ms']:.1f} ms**.\"))"),
          md("## 4. Carga\n\nK3: ECDF; K4: percentiles vs carga; K5: serie temporal en L100 y F2."),
          code("R.k3()"), code("R.k4()"), code("R.k5()"),
          code("R.percentile_table()"),
          md("## 5. Fallas\n\nK6: matriz de rutas; K7: continuidad. La tabla compara la ruta esperada por la Tabla 2 "
             "con la observada."),
          code("R.k6()"), code("R.k7()"), code("R.routes_table()"),
          md("## 6. Hedging\n\nF3H y F3NH reciben las mismas llegadas y demoran las mismas solicitudes; la diferencia se "
             "debe solo a duplicar."),
          code("R.k8()"),
          code("t, diff = R.hedging_table()\ndisplay(t)\nprint({k: round(v, 2) for k, v in diff.items()}, "
               "'<- F3NH menos F3H (ms)')"),
          md("## 7. Fitness functions"),
          code("R.k9()"), code("R.fitness_table()"),
          md("## 8. Limitaciones\n\n- Las dos replicas del reranker son dos instancias del modelo en la misma GPU.\n"
             "- Todo corre en un solo proceso (`asyncio` + hilos) y en una sola maquina (sesion de Kaggle, no Khipu).\n"
             "- El hardware y las latencias absolutas dependen de la GPU de la sesion; C se calibra en la misma maquina.\n"
             "- Con pocas solicitudes por condicion el p99 equivale a un valor cercano al maximo."),
          md("## 9. Conclusion"),
          code("display(Markdown('\\n'.join('- ' + b for b in R.conclusions())))")]
    nb = nbf.v4.new_notebook(cells=c)
    NotebookClient(nb, timeout=600, kernel_name="python3").execute()
    nbf.write(nb, out)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--root", default="results")
    ap.add_argument("--figs", default="figs")
    ap.add_argument("--out")
    a = ap.parse_args()
    out = a.out or f"trabajo{INFO[a.dataset][0]}_latencia_{a.dataset}.ipynb"
    build(a.dataset, a.root, a.figs, out)
