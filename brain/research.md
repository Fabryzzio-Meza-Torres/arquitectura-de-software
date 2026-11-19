# Research experiment memory

## TREC-COVID hybrid-search comparison — 19 November 2026

- Published evidence lives in `paper/resultados/trec-covid-20261119/`: executed notebook, per-query quality, request timings, figures, protocol, portable source and sanitized logs.
- The two pipelines share lexical/semantic retrieval and candidate union; the final ranking uses convex fusion or pointwise Qwen2.5-3B-Instruct scores. The main run used 10,000 sampled documents, 50 queries and 893 candidate pairs.
- All three main Slurm jobs completed successfully. Mean quality favored fusion, but paired confidence intervals included zero. The LLM's measured FP32/A100 MIG latency was much higher. Do not describe this as a demonstrated relevance improvement or as universal LLM inferiority.
- Batch 1 was fastest among 1/4/8 on the measured implementation. Client concurrency with a serialized GPU lane increased queueing without improving throughput; this is not an evaluation of independent model replicas or dynamic batching.
- Preserve failed numerical checks, distinguish a controlled checkpoint replay from production availability, and keep hardware/precision explicit when interpreting latency.
- Public release excludes credentials, private filesystem paths, raw document collections, weights, indexes and checkpoint databases. Publication checksums apply to sanitized copies; original hashes preserve private-source provenance.
- Verification: `python verify_publication.py` checks released file hashes, candidate equality, finite scores, 2,000 successful latency observations and the executed notebook's five error-free code cells. Complementary teammate prompt/coverage analyses are not included in this snapshot.
