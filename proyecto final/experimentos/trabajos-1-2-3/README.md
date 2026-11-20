# MINION integrated evidence

Start with `00_resumen/Resumen_MINION_Trabajos_1_2_3.pdf` (Spanish report) or its editable Markdown source.

- `01_trabajo1/ajuste_dev/`: validated alpha=0.85, development sweep and Slurm evidence.
- `01_trabajo1/relevancia_test/`: executed notebook, figures, raw candidate scores, relevance metrics and paired bootstrap.
- `01_trabajo1/complementarios/`: CPU job 63778, RRF and selective reranking analyses, thresholds and seeds.
- `02_trabajo2_khipu_fiqa/`: original branch `paper/trabajo2`, including pilots and final `results_fiqa_completo_v4/`.
- `03_trabajos2y3_kaggle/`: original branch `feat/khipu-kaggle-results`, FiQA and TREC-COVID Kaggle results and executed notebooks.
- `04_tablas_y_auditoria/`: independently checked request-level summaries, medians/ranges, fitness and provenance.
- `05_trabajo3_khipu_trec/`: pilot, failed capacity attempt, complementary fixed-load run, code, logs, notebook, figures and verification.

The original sources are preserved. Khipu and Kaggle latency series remain separate. Pilots are historical evidence, not final results.
The new `05_trabajo3_khipu_trec/` preserves failed capacity attempt 63911 and a complementary fixed-load run at the same absolute QPS as FiQA. `C_qps=8` in its adapter is an external load scale, NOT a validated TREC capacity. See the Spanish experimental plan and final comparability checks.
`procedencia.json` pins the reviewed branch commits. `MANIFEST_SHA256.json` inventories this package.
No repository branch was changed by this local consolidation. The new TREC benchmark was executed through Slurm on ds001. Original branch sources remain unchanged; the new run and analysis are in folder 05.
