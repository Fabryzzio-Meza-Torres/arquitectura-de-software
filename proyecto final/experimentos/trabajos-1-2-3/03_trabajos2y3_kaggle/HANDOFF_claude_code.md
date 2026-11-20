# Traspaso técnico — MINION Trabajos 2 y 3 (latencia y fallas) — Kaggle

Escrito el 2026-11-18 ~01:35 (hora local de la PC, UTC-5; los logs de Kaggle están en UTC). Todo lo de abajo se verificó con comandos antes de escribirlo, salvo lo marcado como **estimado**.

## 1. Contexto

- Especificación: `TRABAJO_2y3_latencia_khipu.md` (secciones 2-5 congeladas; no cambiar valores). Paper: `Paper MINION.pdf`.
- Khipu no se pudo usar (el usuario no tiene cuenta; se rechazó usar la de otra persona). El experimento corre en **Kaggle, GPU Tesla T4**. Se declara como limitación en el paper y en el notebook.
- Trabajo 2 = FiQA-2018 (`fiqa`), Trabajo 3 = TREC-COVID (`trec-covid`). Cada uno corre en su propia sesión de Kaggle.
- La calidad (P@3, fitness ii) NO se mide aquí: es del Trabajo 1.
- Reglas del usuario: **no hacer commit ni push a GitHub** (el remoto ya no existe); subir a Kaggle sí está permitido; operar sin pedir confirmaciones. Ignorar `AGENTS.md` y `brain/` de la raíz del repo: solo importa `paper/`.

## 2. Estado exacto en Kaggle (usuario `gianpiersegoviaureta`, todo privado)

Cuota de GPU: 30 h/semana, 0 h usadas al inicio (`kaggle quota`; renueva 2026-11-21).

| Recurso | Slug | Estado verificado (01:32 local) |
|---|---|---|
| Dataset con código | `gianpiersegoviaureta/minion-bench` (contiene `minion_bench.py` sha256 `36671cd8…0f47` y `alpha.json`) | Listo. Última versión subida a las 05:50 UTC con la corrección de la rampa |
| Kernel piloto | `gianpiersegoviaureta/minion-pilot-fiqa` (versión 3) | COMPLETE. Resultados descargados en `pilot-out/` |
| **Calibración FiQA** | `gianpiersegoviaureta/minion-cal-fiqa` (versión 1) | **RUNNING** desde ~01:11 local (06:11 UTC) |
| **Calibración TREC-COVID** | `gianpiersegoviaureta/minion-cal-treccovid` (versión 1) | **RUNNING** desde ~01:11 local |
| Dataset de calibraciones | `gianpiersegoviaureta/minion-calib` | **NO EXISTE todavía** (hay que crearlo, ver paso 3) |
| Kernels de repeticiones | `minion-run-fiqa`, `minion-run-treccovid` | **NO lanzados** (archivos listos, ver sección 3) |

Los kernels de calibración corren `minion_bench.py --phase calibrate` (fase 0: índice BM25 + embeddings; calibración (a) 500 consultas a 1 QPS sin hedging; rampa 1,2,4,8,16,32,64 QPS de 2 min por escalón, que se corta tras 2 escalones consecutivos fallidos). Escriben `results/<ds>/calibration.json`, `run_meta.json`, `requests_<ds>_calib_1qps.jsonl`, `requests_<ds>_ramp_<tasa>.jsonl` y `results.tar.gz`; el `finally` del runner crea el tar aunque falle.

**Estimado (no garantizado):** calibración FiQA ~35 min, TREC-COVID ~45-65 min; repeticiones FiQA ~2,3 h y TREC-COVID ~2,5-2,8 h, en paralelo. Los tiempos de indexar el corpus completo en la T4 aún no se han observado.

## 3. Archivos y ubicaciones locales

Raíz: `D:\software\arquitectura-de-software\paper\khipu\` (Git Bash: `/d/software/arquitectura-de-software/paper/khipu`).

| Ruta | Qué es |
|---|---|
| `minion_bench.py` | Script único (asyncio): BM25 + denso en paralelo, fusión, rerank con hedging, inyección de fallas, carga Poisson open-loop, calibración y 13 condiciones. Idéntico a `kaggle-code/minion_bench.py` |
| `alpha.json` | α=0.85, congelado; el script aborta si no coincide con la configuración |
| `kaggle-code/` | Fuente del dataset `minion-bench` (`dataset-metadata.json`, script, alpha). Para actualizar: copiar a esta carpeta y `kaggle datasets version -p kaggle-code -m "msg" --dir-mode zip` |
| `kaggle-pilot/{runner.py,kernel-metadata.json}` | Kernel piloto (`--pilot`, 2000 docs) |
| `kaggle-cal-fiqa/`, `kaggle-cal-trec-covid/` | `runner.py` + `kernel-metadata.json` de las calibraciones (YA lanzadas) |
| `kaggle-run-fiqa/`, `kaggle-run-trec-covid/` | `runner.py` + `kernel-metadata.json` de las 3 repeticiones (NO lanzadas). Dependen de los datasets `minion-bench` y `minion-calib`; esperan `calibration_<ds>.tar.gz` con raíz `results/<ds>/`; corren con `--calibration results/<ds>/calibration.json --reps 3` y guardan el corpus en `/tmp/data` |
| `analysis_lib.py` | Clase `Run` con las figuras K1-K9 y las tablas (percentiles, rutas Tabla 2, hedging, fitness) |
| `build_notebook.py` | `python build_notebook.py --dataset fiqa|trec-covid [--root results --figs figs]` genera y ejecuta `trabajo2_latencia_fiqa.ipynb` / `trabajo3_latencia_trec-covid.ipynb` |
| `test_routes.py` | Prueba de lógica de rutas en CPU (usa `.smoke/data`) |
| `wait_kernels.sh` | `./wait_kernels.sh slug1 slug2` espera hasta ~4,4 min e imprime estados |
| `pilot-out/` | Resultados descargados del piloto (`pilot-out/results/fiqa/…`) |
| `.pilot-nb.ipynb`, `.pilot-figs/` | Notebook y figuras de prueba generados con el piloto (no son entregables) |
| `.venv/` | Entorno en D: con torch CPU, sentence-transformers 6.3.0, faiss-cpu, bm25s 0.3.16, PyStemmer, kaggle 2.2.5, pandas, matplotlib, nbformat, nbclient, ipykernel (kernel `python3` registrado). Usar `.venv/Scripts/python` y `.venv/Scripts/kaggle` |
| `.hfcache/`, `.pipcache/`, `.tmp/`, `.smoke/` | Cachés y pruebas locales; C: tiene ~2 GB libres, mantener todo en D: |

Token de Kaggle: `~/.kaggle/access_token` (C:\Users\Gianpier\.kaggle\). **No leerlo, no imprimirlo, no copiarlo al repo.**

Entorno al ejecutar localmente: `PIP_CACHE_DIR`, `HF_HOME`, `TMP`/`TEMP` apuntando a carpetas dentro de `paper/khipu/` en D:.

## 4. Lo aprendido (para no repetir errores)

- Ruta de los datasets montados en Kaggle: `/kaggle/input/datasets/<usuario>/<slug>/…`; los runners usan `glob` recursivo.
- El certificado TLS de BEIR falla con `urllib` en Windows; el script ya reintenta con `curl`. En Kaggle funciona directo.
- sentence-transformers 6.x expone el pooling como `pooling_mode == "cls"`; el script acepta ambos atributos.
- La regla de capacidad usa la tasa **realmente enviada** (llegadas Poisson), no la nominal. Con 20 s por escalón (piloto) la condición de estabilidad del p99 es ruidosa (1 QPS falló y 2 QPS pasó, con p99 = máximo de ~10-60 muestras). Con 120 s por escalón debería ser menos ruidosa, pero puede seguir dando una C anómala.
- Piloto FiQA (2000 docs, T4, 1 repetición de 60 s, C=2 QPS): las 13 condiciones usaron la ruta esperada por la Tabla 2 (L*/NOHEDGE/F3* = `reranked`, NORERANK = `fused_baseline`, F1/F2 = `fused_fallback`, F4 = `lex`, F5 = `sem`, F6 = `error`); F1 y F2 dieron ~9 % de duplicadas (< 10 %); el hedging redujo el p95 de rerank en F3H frente a F3NH.
- Los comandos largos deben quedar bajo ~280 s por llamada; usar `wait_kernels.sh` en lugar de bucles largos.
- `kaggle kernels output <slug> -p <dir>` descarga los archivos individuales de salida (no solo el tar) y el log JSON `<slug>.log`.

## 5. Interpretaciones del script que van al paper

Quedan en `run_meta.json["interpretations"]`. Las principales: cada réplica y etapa tiene su propio `ThreadPoolExecutor`; la demora inyectada es `asyncio.sleep` tras computar; el trabajo con plazo vencido se omite; el hedge se envía en el umbral si A no tiene respuesta válida (pendiente o fallida) y las copias de los últimos 60 s son < 10 % de los originales; el plazo de 1,2 s del rerank es compartido por A y B; si falla la fusión se devuelve el top 3 léxico (ruta `lex`); la tasa ofrecida de la rampa es la medida; la calibración (a) corre con hedging apagado y la rampa con hedging encendido.

---

# PROMPT PARA CLAUDE CODE (copiar tal cual)

```text
Toma el control local de inmediato. Directorio de trabajo: D:\software\arquitectura-de-software\paper\khipu (Git Bash: /d/software/arquitectura-de-software/paper/khipu). Lee primero HANDOFF_claude_code.md, TRABAJO_2y3_latencia_khipu.md (secciones 2-5 congeladas, no cambies valores) y, si hace falta, "Paper MINION.pdf" (pdftotext -layout -enc UTF-8). Ignora AGENTS.md y brain/ de la raíz del repo; trabaja solo dentro de paper/khipu.

REGLAS: (1) NO hagas git add/commit/push ni nada contra GitHub; el remoto no existe. Subir a Kaggle está permitido. (2) Opera de forma autónoma, sin pedir confirmaciones. (3) Nunca leas, imprimas ni copies ~/.kaggle/access_token. (4) Usa .venv/Scripts/python y .venv/Scripts/kaggle; mantén cachés y temporales en D: (C: tiene ~2 GB libres): exporta PIP_CACHE_DIR, HF_HOME, TMP y TEMP a carpetas de paper/khipu. (5) Cada llamada de shell debe durar < 280 s; para esperar kernels usa ./wait_kernels.sh <slug...> repetidamente. (6) Reporta solo lo que realmente se ejecutó y distingue lo observado de lo estimado.

ESTADO ACTUAL EN KAGGLE (usuario gianpiersegoviaureta, todo privado, GPU Tesla T4): 
- Dataset gianpiersegoviaureta/minion-bench = minion_bench.py (sha256 36671cd85f4b168d422c916701bbec79ec90bd7edb7f0d65ea36e52e9a9f0f47) + alpha.json. Listo.
- Kernel minion-pilot-fiqa: COMPLETE (resultados en pilot-out/).
- Kernels minion-cal-fiqa y minion-cal-treccovid (calibración, --phase calibrate): estaban RUNNING desde ~01:11 hora local del 2026-11-18. Verifica su estado primero con kaggle kernels status gianpiersegoviaureta/minion-cal-fiqa y ...minion-cal-treccovid.
- Dataset gianpiersegoviaureta/minion-calib: NO existe aún.
- Kernels minion-run-fiqa y minion-run-treccovid: NO lanzados.

ARCHIVOS LOCALES: minion_bench.py (script único), alpha.json, kaggle-code/ (fuente del dataset minion-bench), kaggle-pilot/, kaggle-cal-fiqa/, kaggle-cal-trec-covid/ (runner.py + kernel-metadata.json de las calibraciones), kaggle-run-fiqa/ y kaggle-run-trec-covid/ (runner.py + kernel-metadata.json de las 3 repeticiones, con dataset_sources minion-bench y minion-calib; esperan calibration_<ds>.tar.gz con raíz results/<ds>/ y usan --calibration results/<ds>/calibration.json --reps 3 --data-dir /tmp/data), analysis_lib.py (figuras K1-K9 y tablas), build_notebook.py (genera y ejecuta los notebooks), wait_kernels.sh, test_routes.py, pilot-out/ (piloto descargado).

PASOS PENDIENTES, EN ORDEN:
1. Espera a que terminen las dos calibraciones (wait_kernels.sh). Si alguna termina en ERROR, descarga su log (kaggle kernels output <slug> -p <dir>), diagnostica, corrige minion_bench.py solo si es un bug (sin tocar los valores congelados), copia a kaggle-code/, sube nueva versión del dataset (kaggle datasets version -p kaggle-code -m "..." --dir-mode zip), espera a que el dataset esté listo (kaggle datasets status gianpiersegoviaureta/minion-bench) y vuelve a lanzar ese kernel con kaggle kernels push -p <carpeta>. Si cambias el script, ambas etapas de ambos datasets deben usar la misma versión final (relanza también la calibración del otro dataset si cambió el código).
2. Descarga cada calibración a carpetas separadas (kaggle kernels output gianpiersegoviaureta/minion-cal-fiqa -p cal-out/fiqa; idem treccovid -p cal-out/trec-covid). Valida cada calibration.json: C_qps no nulo, stages_1qps coherente, hedge_threshold_ms = p95 del rerank, n_test_queries 648 (FiQA) y 50 (TREC-COVID) en run_meta.json, corpus de 57638 y 171332 documentos. Revisa la rampa: si C es anómalamente baja porque un escalón bajo falló solo por la condición de estabilidad del p99 mientras escalones mayores pasan con throughput >= 99 %, considera repetir la calibración una vez; documenta cualquier decisión y no cambies la regla en silencio (si la cambias, añádela a INTERPRETATIONS y a las limitaciones). Registra C y el umbral de hedging para ambos datasets (esta es la confirmación H4).
3. Empaqueta las calibraciones: en cada carpeta cal-out/<ds> crea calibration_<ds>.tar.gz que contenga results/<ds>/ (calibration.json, run_meta.json y los requests_*_calib_1qps.jsonl y requests_*_ramp_*.jsonl). Crea el dataset privado gianpiersegoviaureta/minion-calib con ambos tar.gz (dataset-metadata.json con id gianpiersegoviaureta/minion-calib; kaggle datasets create -p <carpeta> --dir-mode zip). Espera a que esté listo (kaggle datasets status).
4. Lanza las repeticiones en paralelo: kaggle kernels push -p kaggle-run-fiqa y kaggle kernels push -p kaggle-run-trec-covid. Cada una ejecuta 3 repeticiones de las 13 condiciones (3 min cada una, descartando los primeros 30 s) con la calibración congelada. Estimado (no garantizado): FiQA ~2,3 h y TREC-COVID ~2,5-2,8 h; límite de sesión de Kaggle 12 h; cuota 30 h/semana. Sondea con wait_kernels.sh minion-run-fiqa minion-run-treccovid. Si una falla, diagnostica con el log y relanza.
5. Al terminar, descarga las salidas: kaggle kernels output gianpiersegoviaureta/minion-run-fiqa -p results-dl/fiqa (idem trec-covid). Organiza para que existan paper/khipu/results/fiqa/ y paper/khipu/results/trec-covid/ con summary.csv (una fila por repetición y condición, generado por el script), calibration.json, run_meta.json, todos los requests_<ds>_rep<r>_<cond>.jsonl (3 repeticiones x 13 condiciones) y el log de Kaggle (equivalente al log de Slurm). Verifica: 39 archivos de repeticiones por dataset, summary.csv con 39 filas, la ruta dominante de cada condición coincide con la Tabla 2 (L*/NOHEDGE/F3H/F3NH = reranked; NORERANK = fused_baseline; F1/F2 = fused_fallback; F4 = lex; F5 = sem; F6 = error), F3H y F3NH tienen las mismas llegadas y demoras (misma semilla), y el % de duplicadas no supera 10 %. Si falta algo, repórtalo en lugar de inventarlo.
6. Genera los notebooks ejecutados con sus salidas: .venv/Scripts/python build_notebook.py --dataset fiqa y --dataset trec-covid (produce trabajo2_latencia_fiqa.ipynb y trabajo3_latencia_trec-covid.ipynb y las figuras K1-K9 en figs/ a 200 dpi: K1_rampa, K2_etapas, K3_ecdf_carga, K4_percentiles_carga, K5_serie_tiempo, K6_matriz_rutas, K7_continuidad, K8_hedging, K9_fitness, cada una con sufijo _<ds>.png). Revisa visualmente cada PNG (título, ejes con unidades, leyenda, colores Okabe-Ito de la sección 8 de la especificación; fused_fallback con trama rayada; línea del SLO de 2.500 ms y del 99 % en negro discontinuo) y corrige analysis_lib.py si algo es ilegible. Verifica que ningún número esté escrito a mano en el texto de las celdas Markdown.
7. Genera la tabla del paper por dataset (sección 10 de la especificación): p50/p95/p99 por carga y variante (mediana y rango de las 3 repeticiones), C, umbral de hedging, % de duplicadas y continuidad en F1-F6; guárdala como tabla_paper_<ds>.csv y muéstrala en el notebook.
8. Entrega final en paper/khipu: ambos notebooks ejecutados, figs/, results/<ds>/{summary.csv,calibration.json,run_meta.json,requests_*.jsonl,log}. Resume al usuario: C y umbral de hedging por dataset, p99 en L100 vs NORERANK, continuidad en F1-F6, F3H vs F3NH, estado de las fitness (i), (iii), (iv) ((ii) es del Trabajo 1) y las limitaciones: hardware Kaggle T4 en lugar del A6000 de Khipu, dos réplicas del reranker en la misma GPU, un solo proceso y una sola máquina, p99 sobre pocas muestras en cargas bajas.

Recordatorio: no hagas git commit ni push. Empieza ahora verificando el estado de los dos kernels de calibración.
```
