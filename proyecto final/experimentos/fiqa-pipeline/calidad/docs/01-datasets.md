# Datasets: NFCorpus y TREC-COVID

Usamos dos datasets de BEIR, un benchmark estándar de búsqueda. Cada uno cumple un papel distinto en el paper. Los números reales (verificados con los archivos descargados) están en `04-datasets-verificados.md`.

## Cuál usamos para qué

| Dataset | Papel | Experimentos |
| --- | --- | --- |
| **NFCorpus** | Base: corpus chico, rápido de iterar | E1 a E5 (calidad y latencia) |
| **TREC-COVID** | Escala: corpus unas 47 veces mayor | E6 (qué pasa al crecer) |

El PDF de reparto hablaba de 1 millón de documentos. No lo alcanzamos: nuestro máximo es TREC-COVID, con unos 171 mil. Lo declaramos como limitación.

## Qué contiene cada uno

- **NFCorpus:** preguntas sobre nutrición escritas en lenguaje común, y artículos científicos médicos como documentos. Unos 3,6 mil documentos y 323 queries de prueba.
- **TREC-COVID:** preguntas sobre COVID-19 y artículos científicos sobre el tema. Unos 171 mil documentos pero solo 50 queries.

Ambos vienen en el mismo formato: un archivo de documentos, uno de queries y unos *qrels*, que son los juicios de expertos que dicen qué documentos responden a cada query y con qué grado (0 no, 1 sí, 2 muy relevante).

## Cómo se lee

Cada query tiene **muchos** documentos relevantes (decenas en NFCorpus, cientos en TREC-COVID). Eso importa: para medir si los 3 primeros resultados son buenos (P@3) necesitamos al menos 3 relevantes por query. Un documento sin juicio no se sabe si es malo o simplemente no se revisó; por eso medimos cuántos hay (Hole@10) y revisamos una muestra a mano.

## Por qué los elegimos

- **Muchos relevantes por query y grados:** hace interpretable P@3 y nDCG. Descartamos SciFact porque casi cada query tiene un solo relevante.
- **Tamaños complementarios:** NFCorpus para iterar rápido, TREC-COVID para ver latencia a escala real sin inventar datos.
- **Estándar en la literatura:** nuestros números se pueden comparar con otros trabajos.
- **Ya traen juicios:** no tenemos que juzgar miles de pares a mano.
- **Descartados:** TREC DL (8,8 millones de pasajes, inmanejable) y BRIGHT (muy difícil y con corpus grandes; queda como extensión opcional).

## Cómo los usamos

- Los parámetros se ajustan **solo con el split dev**; los resultados del paper salen **solo del split test**. TREC-COVID solo tiene test, así que ahí no se ajusta nada.
- Todos los métodos usan el mismo corpus y los mismos IDs.
- Los índices se construyen una vez, antes de medir, y no cuentan en la latencia.
- Para E6, submuestras de TREC-COVID con semilla fija que siempre incluyen los documentos con juicio.

## Limitaciones

- Solo inglés y tema biomédico; los documentos son resúmenes limpios, no pdf ni docx reales.
- Juicios incompletos: un buen documento sin juicio cuenta como no relevante.
- TREC-COVID tiene solo 50 queries, así que las comparaciones estadísticas pesan menos.

> **Nota (datos reales):** NFCorpus solo tiene grados 1 y 2 (no hay "no relevante" explícito); TREC-COVID tiene grado -1 en 2 juicios, que se tratan como no relevantes. En NFCorpus la mediana de relevantes es 16 (la media, 38, la inflan pocas consultas) y el 14 % de las consultas tiene menos de 3. Detalle en `04-datasets-verificados.md`.

> **FiQA-2018** (preguntas financieras, 57.638 documentos y 648 consultas de prueba según el texto del paper) se descarga igual que los otros con `download_data.py --datasets fiqa`. Sus estadísticas reales (relevantes por consulta, grados) salen de `dataset_stats.py`; hasta correrlo no se citan cifras. Si tiene pocos relevantes por consulta, P@3 nunca llegará a 1 y conviene leerlo junto con nDCG@3 y MRR@10.
