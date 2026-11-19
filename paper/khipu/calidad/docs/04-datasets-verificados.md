# Datasets verificados: NFCorpus y TREC-COVID

Números reales sacados de `results/<dataset>/stats.json` tras correr `python src/run_all.py` (15-nov-2026). Se contrastan con lo que dice `01-datasets.md`.

## NFCorpus (base)

### Qué contiene

Preguntas de nutrición en lenguaje común y resúmenes de artículos médicos. Son 3.633 documentos (233,8 palabras de media) y 3.237 queries repartidas en train, dev y test. Ejemplo real del split test:

- **Query** `PLAIN-1008`: *"deafness"*
- **Relevante** `MED-4536` (grado 1): *"Potential of traditional ayurvedic formulation, Triphala, as a novel anticancer drug..."*
- **No relevante:** no hay ejemplo, porque el dataset no trae ningún juicio de grado 0.

El ejemplo muestra lo particular de NFCorpus: el documento relevante no menciona la palabra de la query. Los juicios vienen de enlaces indirectos entre artículos, no de una lectura directa.

### Cómo se lee

- **Grados:** solo existen 1 y 2. En test hay 11.758 juicios de grado 1 y 576 de grado 2 (4,7 %). Casi todo es "relevante, sin más".
- **Muchos relevantes:** la media es 38,2 por query, pero la mediana es 16 y el rango va de 1 a 475. Pocas queries muy generales inflan la media. El 85,8 % de las queries tiene al menos 3 relevantes, así que P@3 es interpretable en la mayoría, no en todas.
- **Sin juicio:** como no hay juicios de grado 0, todo documento no listado se cuenta como no relevante. Con BM25, `Hole@10` es 0,640: el 64 % de lo que aparece en el top 10 nunca fue juzgado. Por eso la revisión manual importa más aquí.

## TREC-COVID (escala)

### Qué contiene

Preguntas sobre COVID-19 y artículos científicos del tema. Son 171.332 documentos (161,2 palabras de media), solo 50 queries y solo split test. Ejemplo real:

- **Query** `1`: *"what is the origin of COVID-19"*
- **Relevante** `zxudiyj4` (grado 2): *"Genetic evolution analysis of 2019 novel coronavirus and coronavirus from other species..."*
- **No relevante** `02say5f1` (grado 0): *"COVID-19-related prejudice toward Asian medical students..."*

Habla de COVID, pero no del origen del virus.

### Cómo se lee

- **Grados:** 0 (41.661), 1 (10.456) y 2 (14.217, el 21 %). Hay juicios negativos explícitos, a diferencia de NFCorpus.
- **Muchos relevantes:** 493,5 por query de media, mediana 478, entre 111 y 1.266. El 100 % de las queries tiene al menos 3 relevantes.
- **Sin juicio:** `Hole@10` es 0,118 con BM25. La mayoría de lo que sube al top 10 sí fue juzgado, así que los números son más fiables que en NFCorpus.

## Cómo nos sirven y por qué los elegimos

- **NFCorpus** es corpus chico y rápido: BM25 lo indexa en 0,5 s, ideal para iterar E1 a E5.
- **TREC-COVID** es 47,2 veces mayor (171.332 / 3.633). BM25 lo indexa en 16,8 s, y sirve para E6.
- Ambos traen juicios graduados y varios relevantes por query, que es lo que necesitan P@3 y nDCG. Esto coincide con `01-datasets.md`.

## Estadísticas (split test)

| | NFCorpus | TREC-COVID |
| --- | ---: | ---: |
| Documentos | 3.633 | 171.332 |
| Palabras por documento (media) | 233,8 | 161,2 |
| Queries en test | 323 | 50 |
| Juicios | 12.334 | 66.336 |
| Grados presentes | 1, 2 | -1, 0, 1, 2 |
| Relevantes por query (media / mediana / mín / máx) | 38,2 / 16 / 1 / 475 | 493,5 / 478 / 111 / 1.266 |
| Queries con ≥3 relevantes | 85,8 % | 100 % |
| Juicios sin documento en el corpus | 0 | 0 |
| Hole@10 con BM25 | 0,640 | 0,118 |

## Lo que no coincide con `01-datasets.md`

| `01-datasets.md` dice | Datos reales |
| --- | --- |
| Grados 0, 1 y 2 en ambos | NFCorpus no tiene grado 0; TREC-COVID tiene además grado -1 (2 juicios) |
| "Cada query tiene muchos relevantes" | En NFCorpus el mínimo es 1 y el 14,2 % de las queries de test tiene menos de 3 |
| Decenas de relevantes en NFCorpus | Media 38, pero mediana 16 |
| NFCorpus "323 queries de prueba" | Coincide. Pero 25 de ellas no devuelven resultados con BM25 |

## Control de BM25 y consultas sin resultados

- **Referencia:** BM25 "flat" (título y texto juntos, como el nuestro): NFCorpus 0,322 y TREC-COVID 0,595 (Kamalloo et al. 2023, arXiv 2306.07471). Los 0,325 y 0,656 que usábamos antes son de la variante multifield, que no es comparable.
- **Resultado nuestro:** 0,308 y 0,574. Quedamos 0,014 y 0,021 por debajo, razonable al no usar stemming. No hay evidencia de un error de métricas.
- **Las 25 consultas sin resultados** de NFCorpus son palabras sueltas (`okra`, `Zoloft`, `bagels`, `airport scanners`) cuyo término exacto no aparece en el corpus. Con stemming varias sí coincidirían (`leeks` y `leek`, `bagels` y `bagel`). Puntúan 0, correcto para un sistema léxico puro, y es justo donde la búsqueda semántica debería ayudar. Vale mencionarlo en el paper.
