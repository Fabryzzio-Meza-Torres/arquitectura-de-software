# MINION demo

Demo web (React + Vite + Tailwind + React Bits) que compara la arquitectura A (fusión BM25+BGE) con la B (sLLM Qwen2.5-3B por lotes) usando los resultados reales de `../minion_fiqa_llm_v2`.

```bash
python3 prep_data.py        # regenera app/public/data desde los resultados
cd app && npm install && npm run dev   # http://localhost:5173
```

Los tiempos del flujo se reproducen a partir de las mediciones por consulta; no se ejecuta ningún modelo en vivo.
