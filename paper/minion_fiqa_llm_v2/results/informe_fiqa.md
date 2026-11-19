# MINION — Experimento FiQA con LLM

Fecha de consolidacion: 2026-11-19

## 1. Configuracion

- Dataset: FiQA-2018
- Corpus experimental: 10 000 documentos
- Recuperacion: BM25 top 10 + BGE top 10
- Candidatos: hasta 20 documentos unicos
- Ranking A: fusion convexa, alpha = 0.85
- Ranking B: Qwen2.5-3B-Instruct
- Metricas principales: P@3, nDCG@3, MRR@10
- Metricas adicionales: P@5, nDCG@5

## 2. Calidad

Consultas: 648

| Metrica | Fusion A | Qwen B | Delta B-A | IC 95% |
|---|---:|---:|---:|---|
| p@3 | 0.0823 | 0.0658 | -0.0165 | [-0.0257, -0.0077] |
| ndcg@3 | 0.1933 | 0.1381 | -0.0552 | [-0.0768, -0.0343] |
| p@5 | 0.0562 | 0.0472 | -0.0090 | [-0.0139, -0.0040] |
| ndcg@5 | 0.2039 | 0.1516 | -0.0523 | [-0.0720, -0.0335] |
| mrr@10 | 0.2047 | 0.1495 | -0.0551 | [-0.0748, -0.0347] |

## 3. Batching

| Batch | Repeticiones validas | Tiempo medio (s) | Diferencia maxima |
|---|---:|---:|---:|
| 1 | 3 | 8.422 | 0.00000 |
| 4 | 3 | 8.919 | 0.01949 |
| 8 | 3 | 9.042 | 0.01560 |

Batch seleccionado: 1, segun tolerancia predefinida de 0.001.

## 4. Concurrencia

| Concurrencia | Solicitudes | OK | Throughput | p99 ms |
|---|---:|---:|---:|---:|
| 1 | 50 | 50 | 1.100 | 1169.74 |
| 2 | 50 | 50 | 1.081 | 2134.58 |
| 4 | 50 | 50 | 1.080 | 4063.08 |

## 5. Latencia

| Ranking | Solicitudes | OK | p50 ms | p95 ms | p99 ms | Continuidad |
|---|---:|---:|---:|---:|---:|---:|
| A | 50 | 50 | 23.14 | 31.13 | 431.76 | 100.00% |
| B | 50 | 50 | 930.26 | 1071.55 | 1319.14 | 100.00% |

## 6. Recuperacion

Registrar si se interrumpio efectivamente el job,
el numero de consultas guardadas antes de interrumpir,
el resultado de la reanudacion y la comparacion
contra la referencia.

## 7. Limitaciones

- Corpus reducido de 10 000 documentos.
- Juicios de relevancia incompletos.
- FiQA tiene relevancia principalmente binaria.
- p99 con 50 solicitudes es exploratorio.
- La concurrencia usa una cola conservadora para la GPU.
- El texto enviado al LLM se limita a 384 tokens.
- TREC-COVID tiene otra distribucion de consultas y etiquetas.
