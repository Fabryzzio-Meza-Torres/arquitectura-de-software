# Reglas de evaluación

Todos los experimentos se miden con las mismas reglas (implementadas en `src/metrics.py`). Así las comparaciones del paper son justas y reproducibles.

## Qué es "relevante"

Un documento es relevante si su grado en los juicios es mayor que 0. Si el grado es 0, se juzgó y no sirve. Si no aparece, no se sabe: cuenta como no relevante, pero lo contamos aparte con Hole@10. Es la convención de BEIR y TREC, y nos permite comparar con otros trabajos.

## Métricas

| Métrica | Qué nos dice |
| --- | --- |
| **P@3** (principal) | De los 3 primeros resultados, cuántos son buenos. Es la calidad final que ve el usuario. |
| **nDCG@3 y nDCG@10** | Si lo más relevante está arriba. El @10 es el que reportan los papers de BEIR. |
| **MRR@10** | Qué tan pronto aparece el primer acierto. |
| **Recall@20** | Cuánto de lo bueno entra en los 20 candidatos que recibe el reranker. |
| **Rcap@20** | Lo mismo, pero con tope. Con ~38 relevantes por query, Recall@20 nunca pasa de ~0,5 aunque el sistema sea perfecto; el tope lo corrige. |
| **Suf3@20** | Si los 20 candidatos traen al menos 3 relevantes. Sin eso, el reranker no puede llenar el top-3. |
| **OracleP3@20** | El mejor P@3 que lograría un reranker perfecto con esos candidatos. Separa el error del retrieval del error del reranker. |
| **Hole@10** | Qué parte del top-10 no tiene juicio. Avisa cuando los números pueden estar subestimados. |

## Cómo se promedia

Se promedia sobre **todas** las queries que tienen algún relevante. Si un sistema no responde una query, esa query vale 0, no se descarta: un sistema que falla no debe verse mejor. Los empates se resuelven por ID, para que el resultado sea siempre el mismo.

## Latencia

- Se mide de extremo a extremo por query y se reportan p50, p95 y p99, tomando el valor real observado (sin interpolar).
- Cuentan todas las solicitudes, también las que fallan (`degraded`, `timeout`, `error`). Un sistema rápido porque falla no es bueno.
- **P@3 y p99 siempre se reportan juntos.** Es el eje del paper: cuánta calidad ganamos por cada milisegundo de cola.
- Con ~300 queries, el p99 depende de solo 3 solicitudes. Por eso las pruebas de carga usan **al menos 1.000 solicitudes**, repitiendo las consultas, y se reporta cuántas fueron.
- Se reportan **dos p99**: con todas las solicitudes (`p99_ms`) y solo con las que entregan resultados (`p99_with_results_ms`, la definición del texto del paper). Si difieren mucho, los timeouts y errores están escondiendo la cola; la continuidad ante fallas (consultas con tres resultados en ≤ 2,5 s) cubre ese hueco.
- **Solicitudes adicionales:** duplicadas enviadas ÷ originales, en %. El límite del paper es 10 %. Se cuenta con `r.add_extra()`.

## Cómo comparamos sistemas

- Siempre sobre las mismas queries y de forma pareada (query contra query).
- Reportamos la diferencia con un intervalo de confianza del 95% (bootstrap) y un p-valor (prueba de aleatorización). Con varias métricas a la vez se corrige con Holm para no inflar falsos positivos. La referencia metodológica es Smucker et al., CIKM 2007 (por verificar).
- No basta con "es significativo": contamos cuánto mejora.
- **Base contra propuesta:** además de las medias, se cuenta en cuántas consultas gana cada una y en cuántas gana el léxico solo (`compare_rankings.py`). Las dos leen los mismos one-pagers y parten de los mismos candidatos.
- **Análisis por documento (pointwise):** AUC y Spearman entre el score y el grado de BEIR, solo con documentos juzgados. Esta regla es distinta a la de P@3 (donde lo no juzgado cuenta como no relevante) y se dice en el texto. Es complementario.

## Protocolo

1. Ajustar solo con dev y reportar solo con test.
2. Fijar métricas, splits y semillas antes de correr los experimentos.
3. Revisar a mano una muestra de 30 a 50 queries y reportar los resultados con y sin esos juicios extra.
4. Mostrar siempre el número de queries junto a cada resultado.

## Lo que dejamos fuera

MAP (no aporta sobre nDCG y MRR para un top-3) y Exact Match o F1 (son de respuestas generadas, aquí evaluamos recuperación y reranking).
