# Borrador: sección de datos y evaluación del paper

> **Ojo:** este borrador está escrito con NFCorpus y TREC-COVID. El texto vigente del paper usa FiQA-2018 (57.638 documentos, 648 consultas de prueba) y TREC-COVID; al pasarlo, cambiar los datos de NFCorpus y las cifras de relevantes por consulta (se sacan con `dataset_stats.py`). La comparación base contra propuesta está en `07-comparacion-arquitecturas.md`.
>
> Borrador para refinar. Los números de los datasets ya vienen de `04-datasets-verificados.md`; los que siguen entre ⟦ ⟧ salen de los experimentos. Las referencias marcadas "por verificar" no se han abierto todavía.

## Datos

Evaluamos sobre dos colecciones de BEIR [1], un benchmark estándar de recuperación de información. **NFCorpus** [2] reúne consultas de lenguaje cotidiano sobre nutrición y artículos científicos médicos como documentos (3 633 documentos, 323 consultas de prueba). **TREC-COVID** [3] contiene literatura científica sobre COVID-19 (171 332 documentos, 50 consultas). Ambas traen juicios de relevancia graduados (NFCorpus usa los grados 1 y 2; TREC-COVID, 0 a 2) con muchos documentos relevantes por consulta (38,2 y 493,5 en promedio), lo que permite medir precisión en los primeros resultados.

NFCorpus es la colección base para los experimentos de calidad y latencia. TREC-COVID, unas 47 veces mayor, sirve para estudiar cómo cambia la latencia al crecer el corpus; para ello generamos submuestras anidadas con semilla fija que conservan todos los documentos relevantes. Reconocemos que el corpus planteado inicialmente (un millón de documentos) queda fuera de alcance; el mayor tamaño evaluado es 171 332.

## Protocolo

Los hiperparámetros (pesos de fusión, tamaño de ventana, umbrales del presupuesto de latencia) se ajustan únicamente con el conjunto de desarrollo de NFCorpus. Los resultados se reportan solo sobre el conjunto de prueba. TREC-COVID solo tiene conjunto de prueba, de modo que se usa sin ajustes, con la configuración fijada en NFCorpus; esto mide también la capacidad de generalizar. Métricas, particiones y semillas se fijaron antes de ejecutar los experimentos.

## Métricas

La calidad final se mide con **Precision@3**, complementada con nDCG@3, nDCG@10 (comparable con otros trabajos sobre BEIR) y MRR@10. Para la etapa de recuperación reportamos Recall@20 y una versión con tope, ya que con decenas de relevantes por consulta el recall clásico no puede alcanzar 1. Añadimos dos diagnósticos sobre los 20 candidatos que recibe el reranker: la fracción de consultas con al menos tres relevantes entre ellos, y el techo de Precision@3 que lograría un reranker perfecto. Así se separa el error de recuperación del error de reordenamiento. Las consultas sin respuesta puntúan cero; ninguna se descarta.

Consideramos relevante un documento con grado mayor que cero. Los documentos sin juicio se tratan como no relevantes, pero cuantificamos su presencia en el top-10 y revisamos manualmente una muestra de ⟦30 a 50⟧ consultas para estimar cuánto afectan los resultados.

## Latencia

Medimos la latencia de extremo a extremo por consulta (búsqueda, fusión, reranking y espera en cola; sin construir índices) y reportamos p50, p95 y p99 por rango más cercano. Todas las solicitudes cuentan, también las que terminan en degradación, tiempo agotado o error, que reportamos como fracciones aparte. Cada resultado de calidad se presenta junto con su p99. Dado que con unos cientos de consultas el p99 depende de pocas observaciones, repetimos cada corrida ⟦N⟧ veces.

## Comparación estadística

Comparamos sistemas de forma pareada sobre las mismas consultas. Reportamos la diferencia media con un intervalo de confianza del 95% por bootstrap pareado (10 000 remuestreos) y el p-valor de una prueba de aleatorización pareada, práctica recomendada en evaluación de recuperación de información [4]. Al comparar varias métricas aplicamos la corrección de Holm.

## Amenazas a la validez

- **Dominio e idioma:** ambas colecciones son biomédicas y en inglés; los resultados pueden no generalizar a otros dominios.
- **Documentos limpios:** los textos son resúmenes y no archivos pdf o docx, así que no medimos errores de extracción.
- **Juicios incompletos:** un documento relevante sin juicio cuenta como no relevante; mitigado con Hole@10 y la revisión manual.
- **Pocas consultas en TREC-COVID** (50): las pruebas estadísticas tienen poca potencia.
- **Submuestras:** al conservar todos los relevantes, los corpus pequeños son proporcionalmente más fáciles; comparamos calidad solo dentro de un mismo tamaño y usamos el tamaño para estudiar latencia.

## Reproducibilidad

Los datos se descargan con huellas md5 y sha256 registradas, los scripts de evaluación son comunes a todos los experimentos y están cubiertos por pruebas con casos calculados a mano, y las semillas se fijan en el muestreo y en las pruebas estadísticas.

## Referencias

1. N. Thakur et al., "BEIR: A heterogeneous benchmark for zero-shot evaluation of information retrieval models," NeurIPS Datasets and Benchmarks Track, 2021. arXiv:2104.08663.
2. V. Boteva et al., NFCorpus, 2016. **Por verificar** título, venue y año.
3. E. Voorhees et al., TREC-COVID, 2021. **Por verificar** título y venue.
4. M. Smucker, J. Allan, B. Carterette, "A comparison of statistical significance tests for information retrieval evaluation," CIKM 2007. **Por verificar.**
