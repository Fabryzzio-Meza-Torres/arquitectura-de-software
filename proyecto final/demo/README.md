# MINION · Evidence Lab

Demo de escritorio alineada al paper: baseline semántico, fusión convexa y scoring Qwen, con los top 3 de 50 consultas TREC-COVID y 648 consultas FiQA. Incluye métricas, intervalos guardados, detalle de documentos y una explicación interactiva del estudio complementario MiniLM con fallback y hedging.

## Abrir

Los datos exportados están incluidos; no requiere GPU, credenciales ni modelos.

```bash
cd app
npm ci --ignore-scripts
npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
# http://127.0.0.1:5174/
npm run build
```

La entrada actual es `app/src/PaperApp.tsx`; `App.tsx` conserva la implementación anterior. El diseño prioriza escritorio (ancho mínimo 1120 px).

## Qué representa

- Reproduce rankings guardados; no hace búsquedas nuevas ni inferencia en vivo. La animación comprime el recorrido y no mide latencia.
- La fusión usa 15 % léxico y 85 % semántico. Fusión y Qwen comparten la unión original de candidatos; el baseline recupera su propio top 10 semántico.
- Los scores de modelos no son probabilidades calibradas. Los juicios oficiales se muestran aparte; un documento sin juicio no se etiqueta como irrelevante.
- Los textos visibles son extractos de hasta 2400 caracteres, no una afirmación sobre cuánto texto procesó el experimento original.
- Los tiempos son estadísticas del estudio, no tiempos medidos por consulta en el navegador. Qwen pertenece a la corrida original; la comparación de latencia emparejada corresponde al baseline y fusión del nuevo control.
- MiniLM es un cross-encoder distinto de Qwen y fue evaluado sobre corpus completos. Su tabla es complementaria y no comparte la muestra de 10 000 documentos.
- Cada colección abre con el primer caso del grupo donde la fusión supera a semántica y a Qwen en P@3. Le siguen las consultas donde supera a un solo método y luego las demás. Dentro de cada grupo se ordena por la menor de las dos diferencias de P@3, luego por la suma de ambas y por ID. Las métricas globales incluyen todas las consultas.
- La interfaz reutiliza la aurora, el título animado y las tarjetas Spotlight de la demo original, con turquesa para fusión y violeta para Qwen.

## Regenerar los datos

`prep_paper_data.py` usa solamente la biblioteca estándar de Python:

```bash
python prep_paper_data.py --trec /ruta/experimentos_cientificos_20261119 --fiqa /ruta/minion_fiqa_llm_v2 --baseline /ruta/baseline_semantico_20261119
```

Exporta `app/public/paperdata/manifest.json` y un JSON por consulta. Las fuentes y estadísticas quedan registradas en el manifest. Los archivos grandes de corpus, modelos y credenciales no se necesitan para servir la demo.

Los insumos de regeneración incluyen los corpus muestreados, que se preparan con los scripts de los experimentos.
