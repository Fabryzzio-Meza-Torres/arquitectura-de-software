# Solo semántica: fiqa

Corrida completa

[
  {
    "method": "semantic",
    "P3": 0.08230452674897118,
    "nDCG3": 0.18842594439339078,
    "MRR10": 0.1969582843425436
  },
  {
    "method": "fusion_matched",
    "P3": 0.08230452674897118,
    "nDCG3": 0.19353778319911424,
    "MRR10": 0.20500624632569076
  },
  {
    "method": "fusion_reference",
    "P3": 0.08230452674897118,
    "nDCG3": 0.19333573111026942,
    "MRR10": 0.20465473740936707
  },
  {
    "method": "LLM_reference",
    "P3": 0.06584362139917695,
    "nDCG3": 0.13810536134114465,
    "MRR10": 0.14953030080344895
  }
]

Comparaciones pareadas: diferencias_pareadas.csv. Los IC que incluyen cero no prueban igualdad.

La latencia compara solo semántica y fusión recalculada en el mismo job. El LLM se conserva como referencia de calidad, sin repetir su inferencia.

Las diferencias del control frente a la fusión anterior se conservan; no se ocultan ni se atribuyen solo a un factor.