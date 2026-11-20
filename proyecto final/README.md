# MINION · Entrega final

MINION compara tres formas de recuperar y ordenar documentos para responder consultas técnicas. El baseline usa búsqueda semántica. Las dos alternativas recuperan en paralelo con BM25 y BGE, unen los candidatos por ID y los ordenan mediante fusión convexa o puntuación individual con Qwen. Un estudio complementario evalúa MiniLM como cross-encoder después de la fusión, además de fallback y hedging.

- [Paper final](paper/MINION.pdf) y [figuras editables](paper/figuras/)
- [Demo pública de escritorio](https://minion-evidence-lab.pages.dev/) y [código de la demo](demo/)
- [Resumen de los trabajos 1, 2 y 3](experimentos/trabajos-1-2-3/00_resumen/Resumen_MINION_Trabajos_1_2_3.md)
- [Procedencia de las ramas](PROCEDENCIA.json)

## Qué encontró el equipo

La fusión usa **85 % semántico y 15 % léxico** tras normalizar los dos scores por consulta. El equipo fijó α en FiQA-dev con 500 consultas y el corpus completo. La selección por P@3, nDCG@3 y menor α produjo 0,85, con P@3 de 0,2513 y nDCG@3 de 0,4027.

| Evaluación con 10.000 documentos | Semántica P@3 | Fusión P@3 | Qwen P@3 |
| --- | ---: | ---: | ---: |
| TREC-COVID, 50 consultas | 0,6133 | **0,6867** | 0,6667 |
| FiQA-test, 648 consultas | **0,0823** | **0,0823** | 0,0658 |

En TREC-COVID, el control emparejado estimó una mejora de **7,33 puntos porcentuales** de P@3 frente a semántica sola (IC 95 % de +3,33 a +11,33). En FiQA-test, la fusión empató en P@3 y mejoró MRR@10 en 0,0080 (IC 95 % de +0,0025 a +0,0141). Qwen obtuvo menor P@3 que la fusión en ambas muestras. Los resultados de MiniLM corresponden a corpus completos y tampoco demostraron una mejora al añadir el cross-encoder. La evaluación de continuidad y latencia bajo fallas responde a una pregunta operativa separada.

## Evidencia experimental

| Carpeta | Contenido |
| --- | --- |
| [trabajos-1-2-3](experimentos/trabajos-1-2-3/) | Ajuste de α, relevancia de corpus completos, RRF y reranking selectivo, carga, fallas y hedging. Incluye las corridas de Khipu y Kaggle y sus notebooks. |
| [trec-covid](experimentos/trec-covid/) | Fusión frente a Qwen en la muestra de TREC-COVID, con notebook ejecutado, scores, rankings, intervalos, rendimiento, recuperación y logs de Slurm. |
| [fiqa](experimentos/fiqa/) | Resultados equivalentes del equipo para FiQA, con código, métricas por consulta y mediciones de rendimiento. |
| [fiqa-pipeline](experimentos/fiqa-pipeline/) | Protocolo y herramientas de comparación de la rama del equipo. |
| [baseline-semantico](experimentos/baseline-semantico/) | Baseline y control de fusión para ambos conjuntos. Incluye P@3, nDCG@3, MRR@10, IC pareados, p95, p99, rankings y notebooks. |

El [alpha.json validado](experimentos/trabajos-1-2-3/01_trabajo1/ajuste_dev/alpha.json) identifica la corrida de ajuste. Las muestras de 10.000 documentos, los corpus completos y las mediciones entre plataformas se interpretan dentro de sus respectivos protocolos. La demo permite explorar las consultas y los scores guardados. Muestra los juicios oficiales de relevancia por separado.

## Reproducir la demo

Desde esta carpeta, con Node.js 22.12 o posterior:

```bash
cd demo/app
npm ci --ignore-scripts
npm run dev
npm run build
```

Las consultas y scores que la demo necesita ya están incluidos. Para volver a ejecutar experimentos, sigue el README de cada corrida y configura tus rutas de datos, modelos y Slurm. Se incluyen códigos, configuraciones registradas, métricas y evidencias. Los corpus completos, pesos, índices regenerables, cachés, credenciales y archivos duplicados de empaquetado quedan fuera.

Las rutas personales de Khipu se sustituyeron por rutas de ejemplo en las copias correspondientes. Los hashes históricos de ejecución identifican los originales, mientras que el manifiesto público de TREC-COVID valida los archivos de ese paquete.
