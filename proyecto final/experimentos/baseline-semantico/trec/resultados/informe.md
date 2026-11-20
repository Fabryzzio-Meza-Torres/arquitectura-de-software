# Solo semántica: trec

Corrida completa

[
  {
    "method": "semantic",
    "P3": 0.6133333333333333,
    "nDCG3": 0.5927753052962159,
    "MRR10": 0.8743333333333332
  },
  {
    "method": "fusion_matched",
    "P3": 0.6866666666666668,
    "nDCG3": 0.6401870004102319,
    "MRR10": 0.8856666666666666
  },
  {
    "method": "fusion_reference",
    "P3": 0.6866666666666668,
    "nDCG3": 0.6401870004102319,
    "MRR10": 0.8856666666666666
  },
  {
    "method": "LLM_reference",
    "P3": 0.6666666666666665,
    "nDCG3": 0.6179519150681838,
    "MRR10": 0.8445555555555555
  }
]

Comparaciones pareadas: diferencias_pareadas.csv. Los IC que incluyen cero no prueban igualdad.

La latencia compara solo semántica y fusión recalculada en el mismo job. El LLM se conserva como referencia de calidad, sin repetir su inferencia.

Las diferencias del control frente a la fusión anterior se conservan; no se ocultan ni se atribuyen solo a un factor.