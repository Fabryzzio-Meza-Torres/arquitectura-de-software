from pathlib import Path
import json,html,shutil
import pandas as pd
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/MINION_integrado'; DOC=OUT/'00_resumen'; DOC.mkdir(exist_ok=True)
T=OUT/'04_tablas_y_auditoria'
lat=pd.read_csv(T/'latencia_mediana_y_rango.csv'); reps=pd.read_csv(T/'latencia_por_repeticion.csv')
fitness=pd.read_csv(T/'fitness_por_repeticion.csv')
quality=pd.read_csv(OUT/'01_trabajo1/relevancia_test/metrics.csv')
boot=pd.read_csv(OUT/'01_trabajo1/relevancia_test/bootstrap.csv')
C=OUT/'01_trabajo1/complementarios/resultados'
inventory=json.loads((T/'inventario_series.json').read_text())
assert all(x['script_matches_metadata'] for x in inventory)
assert pd.read_csv(T/'verificacion_summaries.csv').select_dtypes('bool').all().all()
pages=[]; current=[]
def page(title):
    global current
    current=[]; pages.append((title,current))
def p(text): current.append(('p',text))
def h(text): current.append(('h',text))
def table(headers,rows,widths=None): current.append(('table',(headers,rows,widths)))
def f(v,n=3): return f'{v:.{n}f}'.replace('.',',')
def ci(lo,hi,n=2,scale=1): return f'[{f(lo*scale,n)}; {f(hi*scale,n)}]'
def l(series,condition): return lat[(lat.series==series)&(lat.condition==condition)].iloc[0]
def range_ms(r): return f"{f(r.p99_ms_median,1)} [{f(r.p99_ms_min,1)}; {f(r.p99_ms_max,1)}]"

page('Resumen integrado de los tres trabajos MINION')
p('18 de noviembre de 2026 · Relevancia offline, latencia y tolerancia a fallas')
p('La evidencia respalda la continuidad del servicio dentro del presupuesto de 2,5 segundos en las condiciones medidas, pero no demuestra una mejora de relevancia al añadir el cross-encoder. FiQA pierde P@3 con un intervalo pareado negativo; en TREC-COVID el efecto sigue siendo incierto. El beneficio del hedging depende del montaje y no se reproduce de forma consistente en Khipu.')
h('Qué aporta cada trabajo')
table(['Trabajo','Contenido verificado','Montaje'],[
 ['1','α definitivo y relevancia en FiQA-test y TREC-COVID','Khipu ag001 · A100 MIG 10 GB'],
 ['2','Latencia y fallas de FiQA · 3 repeticiones × 13 condiciones','Khipu ds001 · RTX A6000 compartida'],
 ['3','Latencia y fallas de TREC-COVID · 3 × 13 condiciones','Kaggle · Tesla T4'],
 ['Serie adicional','FiQA · 3 × 13 condiciones con el mismo script de Kaggle','Kaggle · Tesla T4']],[65,255,182])
p('La serie FiQA/Kaggle permite interpretar TREC-COVID dentro de ese montaje. Sus cifras no se mezclan con FiQA/Khipu. Falta ejecutar Trabajo 3 en ds001 con el mismo script v4 y condiciones de recursos para completar el contraste en Khipu.')
h('Conclusiones principales')
table(['Pregunta','Resultado e interpretación'],[
 ['¿Mejora el reranking la relevancia?','FiQA: ΔP@3 = −2,06 puntos porcentuales; IC 95 % [−3,55; −0,57]. TREC-COVID: −2,67 pp; IC [−9,33; +3,33].'],
 ['¿Se cumple p99 ≤ 2500 ms?','Sí en las tres repeticiones de cada serie de latencia, en L25–L100. Es evidencia del montaje medido, no una garantía general.'],
 ['¿Funcionan las rutas de respaldo?','F1 y F2 mantienen 100 % de continuidad en todas las series. F6 devuelve error controlado y tiene 0 % de continuidad, como se esperaba.'],
 ['¿Se respeta el 10 % de duplicadas?','FiQA/Khipu y FiQA/Kaggle: sí en las condiciones de fitness. TREC/Kaggle: no en dos repeticiones, con 10,112 % en L25.']],[130,372])
h('Cómo leer las estadísticas')
p('Relevancia: promedios macro por consulta e intervalos percentiles del 95 % con 10.000 remuestreos pareados. Latencia: mediana del p99 de las tres repeticiones y rango mínimo–máximo. Ese rango no es un intervalo de confianza. Los percentiles se reconstruyeron como el elemento ordenado en la posición ceil(0,99 × N), descartando los primeros 30 segundos.')
p('Las tablas completas y los archivos originales están reunidos en este paquete. El resumen utiliza las corridas finales; los pilotos y diagnósticos se conservan como historial.')

page('Trabajo 1 Relevancia y valor definitivo de alfa')
p('Se fijó α = 0,85 en 500 consultas de FiQA-dev, sobre 57.638 documentos. Entre 21 valores, fue el máximo único de P@3: 0,251333, con nDCG@3 de 0,402684. Los tests no se usaron para ajustar α.')
h('Resultados de prueba')
rows=[]
for ds in ['fiqa','trec-covid']:
    for route in ['fused','reranked']:
        r=quality[(quality.dataset==ds)&(quality.route==route)].iloc[0]
        rows.append([ds,route,f(r.precision_at_3,5),f(r.ndcg_at_3,5),f(r.mrr_at_10,5)])
table(['Dataset','Lista','P@3','nDCG@3','MRR@10'],rows,[100,90,100,105,107])
p('FiQA-test contiene 648 consultas y TREC-COVID 50, sobre sus corpus completos de 57.638 y 171.332 documentos. En ambas listas se conserva exactamente la unión de top 10 BM25 y top 10 semántico, con ambos puntajes calculados para todos los candidatos. Solo cambia su orden al aplicar el cross-encoder.')
rows=[]
for _,r in boot.iterrows(): rows.append([r.dataset,f(100*r.delta_precision_at_3,2),ci(r.ci_95_low,r.ci_95_high,2,100), 'Negativo' if r.ci_95_high<0 else 'Incluye cero'])
table(['Dataset','ΔP@3 en pp','IC pareado 95 % en pp','Lectura'],rows,[100,100,180,122])
p('La fitness de que el reranker no reduzca P@3 no se cumple en la estimación puntual de ninguno de los tests. FiQA presenta evidencia de caída según sus qrels; el intervalo de TREC-COVID no permite afirmar una mejora ni una caída concluyente. Esto no prueba que todo cross-encoder sea peor: el resultado corresponde al modelo MiniLM y a la configuración congelada.')
h('Cobertura de juicios y límites')
p('Recall@20 de fused: 0,53050 en FiQA y 0,03392 en TREC-COVID; solo se promedian consultas con relevantes. El reranker no puede recuperar documentos ausentes de la unión de candidatos.')
table(['Dataset','Judged@10 fused','Judged@10 reranked','ΔP@3 condensada'],[
 ['FiQA','11,59 %','10,63 %','0,00000'],['TREC-COVID','93,80 %','96,80 %','−0,02667']],[105,125,140,132])
p('FiQA solo contiene juicios positivos. Al quitar los documentos no juzgados, la P@3 condensada de dos ordenaciones de los mismos candidatos necesariamente empata; ese cero es estructural y no demuestra ausencia de sesgo. TREC-COVID conserva el signo negativo al condensar. Sus dos entradas −1 se mantuvieron y no aparecieron entre los candidatos recuperados.')
h('Evidencia de ejecución')
p('Ajuste dev: job 63761, ag001, 6 min 10 s. Evaluación test y notebook: job 63769, ag001, 19 min 45 s. El notebook contiene 29 celdas de código ejecutadas, 15 figuras embebidas y cero errores. La copia local y los artefactos se verificaron mediante SHA-256.')
p('Fuentes: 01_trabajo1/ajuste_dev/alpha.json y alpha_curve.csv; 01_trabajo1/relevancia_test/metrics.csv, bootstrap.csv, judged.csv, condensed.csv y final_verification.json.')

page('Trabajo 2 Latencia y fallas de FiQA en Khipu')
p('La corrida final v4 es el job 63828, en ds001 con RTX A6000 compartida, 4 CPU/hilos y 32 GB de RAM solicitados. Se midieron 13 condiciones durante 180 segundos, con descarte de 30 segundos, en tres repeticiones. Hay 39 archivos de solicitudes y 39 filas de resumen.')
h('Capacidad y tiempos observados')
p('La calibración fija C = 8 QPS para la ruta completa reranked, con umbral de hedging de 140,397 ms. Un diagnóstico separado alcanza 64 QPS aceptando otras rutas. Esos 64 QPS no son la capacidad de la ruta completa. En v4, C queda limitado por el primer escalón fallido; esta definición debe mantenerse al repetir TREC-COVID.')
rows=[]
for cond,label in [('L25','25 % de C · 2 QPS'),('L50','50 % · 4 QPS'),('L75','75 % · 6 QPS'),('L100','100 % · 8 QPS'),('NORERANK','Sin reranking · 8 QPS'),('F1','Reranker falla · 6 QPS'),('F2','Reranker lento · 6 QPS')]:
    r=l('fiqa_khipu',cond); rows.append([cond,label,range_ms(r),f(r.continuity_pct_min,1)+' %'])
table(['Condición','Carga o falla','p99 mediana [rango] ms','Continuidad mínima'],rows,[65,145,192,100])
p('L100 reduce el presupuesto disponible de reranking: 4,47 %, 5,38 % y 8,79 % de las solicitudes terminan en fused_fallback, aunque todas entregan tres resultados antes de 2,5 s. El 6,21 % es el promedio de esos porcentajes. La continuidad del 100 % no implica que el 100 % haya recibido el reranker.')
h('Hedging bajo demoras inyectadas')
rows=[]
for rep in [1,2,3]:
    a=reps[(reps.series=='fiqa_khipu')&(reps.rep==rep)].set_index('condition')
    H=a.loc['F3H','p99_ms']; NH=a.loc['F3NH','p99_ms']
    rows.append([str(rep),f(H,1),f(NH,1),f(NH-H,1)])
table(['Repetición','p99 con hedge ms','p99 sin hedge ms','Reducción por hedge ms'],rows,[75,140,140,147])
p('El hedge mejora el p99 en una de las tres repeticiones y lo empeora en dos. Las medianas son 1091,1 ms con hedge y 1061,1 ms sin él. No hay evidencia consistente de beneficio en este montaje. Las llegadas, consultas y banderas de demora coinciden exactamente entre F3H y F3NH en cada repetición.')
p('Fitness (i), (iii) y (iv): cumplen en las tres repeticiones. La mayor proporción de duplicadas en las condiciones de fitness es 9,883 %. F4 vuelve a léxico y F5 a semántico; F6 devuelve error. La GPU tenía otro proceso activo, por lo que no se puede atribuir la diferencia frente a Kaggle solo al modelo de GPU.')
p('Fuente: 02_trabajo2_khipu_fiqa/results_fiqa_completo_v4/ y logs/fiqa-completo-v4-63828.out. Los percentiles se recalcularon desde las solicitudes; el script coincide con la huella registrada al normalizar CRLF a LF.')

page('Trabajo 3 TREC COVID y serie FiQA en Kaggle')
p('La rama feat/khipu-kaggle-results contiene dos series completas en Tesla T4: FiQA y TREC-COVID, cada una con 39 condiciones, tres repeticiones y un notebook ejecutado sin errores. Ambas usan C = 2 QPS. Los umbrales de hedging son 168,069 ms en FiQA y 162,169 ms en TREC-COVID.')
h('Resultados operativos por montaje')
rows=[]
for series,name in [('fiqa_kaggle','FiQA · Kaggle'),('trec-covid_kaggle','TREC · Kaggle')]:
    for cond in ['L100','NORERANK','F3H','F3NH','F2']:
        r=l(series,cond); rows.append([name,cond,range_ms(r),f(r.continuity_pct_min,1)+' %'])
table(['Serie','Condición','p99 mediana [rango] ms','Continuidad mínima'],rows,[100,72,220,110])
p('El hedging reduce la mediana de p99 de F3NH a F3H en 558,1 ms para FiQA y 551,0 ms para TREC-COVID, aproximadamente 58,9 % y 56,0 %, respectivamente. La reducción aparece en las tres repeticiones de cada dataset. Estos resultados describen Kaggle/T4 a 75 % de su C; no se trasladan a ds001, donde la carga absoluta y el comportamiento del hedge son diferentes.')
h('Duplicación y fitness')
p('En TREC-COVID, L25 registra 8/89 = 8,989 % de duplicadas en la primera repetición y 9/89 = 10,112 % en las otras dos. Por ello la fitness (iv) falla en 2 de 3 repeticiones. Las fitness (i) y (iii) cumplen en las tres; F1/F2 mantienen 100 % de continuidad. FiQA/Kaggle cumple (i), (iii) y (iv) en las tres.')
p('El código de Kaggle comprueba la razón de copias antes de añadir la siguiente; con conteos discretos puede admitir una copia que lleve la razón por encima del límite. También el porcentaje global después del calentamiento difiere de una razón móvil de 60 segundos. El código v4 de Khipu comprueba el efecto de añadir la copia y controla además el denominador poscalentamiento. No son implementaciones idénticas del limitador.')
h('Comparación que todavía falta')
p('TREC-COVID aún no tiene una corrida de latencia en ds001 en las ramas revisadas. La comparación FiQA/Khipu contra TREC/Kaggle mezcla dataset, GPU, entorno, carga y reglas de calibración. La serie FiQA/Kaggle sirve como contexto interno de Kaggle, pero no resuelve ese contraste para Khipu.')
p('Fuentes: 03_trabajos2y3_kaggle/results/fiqa/ y results/trec-covid/, tabla_paper_*.csv y los dos notebooks. El documento HANDOFF corresponde a un estado anterior; prevalecen las corridas y metadatos finales que sí están guardados.')

page('Experimentos complementarios de fusión y selección')
p('El job CPU 63778 terminó correctamente en n005 en 8 segundos. Reutilizó los puntajes y rankings guardados, sin ejecutar modelos. Estos análisis complementan el Trabajo 1 y no sustituyen sus resultados principales ni miden latencia.')
h('Combinación convexa frente a RRF')
p('RRF usa k = 60 y las posiciones originales desde 1 de los top 10 léxico y semántico. Una ausencia aporta cero. Se verificó la misma unión de candidatos por consulta; los empates se resuelven por ID ascendente.')
rows=[]
for ds in ['fiqa','trec-covid']:
    d=pd.read_csv(C/f'rrf_paired_differences_{ds}.csv').set_index('metric')
    for metric,label in [('precision_at_3','P@3'),('ndcg_at_3','nDCG@3')]:
        r=d.loc[metric]; rows.append([ds,label,f(r.mean_difference,5),ci(r.ci_95_low,r.ci_95_high,5)])
table(['Dataset','Métrica','Δ RRF menos convexa','IC pareado 95 %'],rows,[100,65,150,187])
p('RRF resulta inferior en P@3 y nDCG@3 en ambos datasets; los cuatro intervalos excluyen cero. Esta conclusión se limita a k = 60, dos listas top 10 y la configuración α = 0,85 ya fijada. No demuestra que RRF sea inferior en otros tamaños de listas o colecciones.')
h('Reranking selectivo con meta principal del 50 por ciento')
p('La política invoca el reranker cuando el margen fusionado entre los puestos 3 y 4 es pequeño; con menos de cuatro candidatos devuelve la fusión. Los umbrales 0,01090972, 0,02539713 y 0,05134022 se congelaron en FiQA-dev para metas de 25 %, 50 % y 75 %. No se ajustaron en test.')
rows=[]
for ds in ['fiqa','trec-covid']:
    m=pd.read_csv(C/f'selective_metrics_{ds}.csv')
    for policy,name in [('fused','Fusión'),('full_reranking','Completo'),('selective','Selectivo meta 50 %'),('random_mean_100','Aleatorio media 100')]:
        sub=m[m.policy==policy]
        if policy in ['selective','random_mean_100']: sub=sub[sub.target_rate==.5]
        r=sub.iloc[0]; rows.append([ds,name,f(r.precision_at_3,5),f(r.ndcg_at_3,5),f(100*r.actual_invocation_rate,1)+' %'])
table(['Dataset','Política','P@3','nDCG@3','Invocaciones'],rows,[88,165,79,85,85])
p('La meta 50 % se convierte en 51,85 % de invocaciones en FiQA y 72 % en TREC-COVID: hay cambio de distribución de márgenes. Frente a fusión sola, ΔP@3 es −0,00463 en FiQA, IC [−0,01543; +0,00669], y −0,01333 en TREC, IC [−0,06667; +0,04000]. Los intervalos incluyen cero; esto no prueba equivalencia ni no inferioridad.')
p('Frente al control aleatorio con exactamente las mismas invocaciones y 100 semillas, las ventajas medias de P@3 son +0,00548 y +0,00460, con IC que también incluyen cero. Esos IC son condicionales al promedio de 100 selecciones, no un bootstrap jerárquico. Reducir invocaciones no permite cuantificar un ahorro de latencia: esa variante requiere una prueba temporal aparte.')

page('Auditoría de procedencia y siguiente corrida comparable')
h('Ramas y fuentes preservadas')
table(['Rama y commit','Contenido relevante'],[
 ['main · f749842d9437','Base común del repositorio; sin los resultados del paper añadidos en las otras ramas.'],
 ['paper/trabajo2 · 650c992c4dd6','FiQA/Khipu v4 final, calibración, scripts, 39 condiciones y logs; conserva pilotos previos.'],
 ['feat/khipu-kaggle-results · 45e4db4e0cdf','FiQA y TREC-COVID en Kaggle, calibraciones, 78 condiciones, 18 figuras K1–K9 y dos notebooks.']],[205,297])
p('Repositorio: github.com/Fabryzzio-Meza-Torres/arquitectura-de-software. Las copias se tomaron de esos commits; las ramas originales no fueron modificadas. procedencia.json y MANIFEST_SHA256.json permiten identificar origen y contenido de la consolidación.')
h('Comprobaciones realizadas')
p('Se revisaron 117 filas de resumen frente a los logs poscalentamiento: p50, p95, p99 y continuidad coinciden dentro del redondeo publicado. Para duplicadas, Khipu usa 0 cuando no se invoca el reranker; la tabla integrada muestra no aplicable en ese caso. Los nueve pares F3H/F3NH tienen idénticas consultas, llegadas y banderas de demora. Las huellas del código coinciden con metadatos, admitiendo la conversión de finales de línea CRLF/LF en la copia de Khipu.')
p('Se conservaron los datos originales y se añadieron tablas normalizadas. No se combinaron latencias de GPUs diferentes, no se reentrenaron modelos y no se reinterpretaron pilotos como corridas finales. La ejecución de los dos notebooks de Kaggle y del notebook del Trabajo 1 se comprobó por sus contadores y salidas, sin volver a correr inferencias.')
h('Qué debe correr el compañero en ds001')
p('<b>Trabajo 3 de latencia y fallas con TREC-COVID</b>, usando el mismo script v4 de paper/trabajo2. Mantener α = 0,85, nodo ds001, RTX A6000, 4 CPU/hilos, 32 GB, la misma solicitud de GPU compartida, 3 repeticiones, 180 segundos por condición y descarte de 30 segundos. Cambiar solo dataset y carpeta de salida, y calibrar nuevamente C y el umbral de hedging para TREC-COVID.')
p('Usar todas las 13 condiciones; verificar 171.332 documentos y 50 consultas test; conservar la misma definición v4 de capacidad de ruta completa y la versión del limitador de duplicadas. Registrar versiones, script SHA-256, nvidia-smi, otros procesos, estado de la GPU, calibración, los 39 archivos de solicitudes, summary.csv y log Slurm. Mismo nodo no implica misma contención: documentar la carga concurrente y no copiar C = 8 QPS de FiQA.')
h('Decisión que sostiene la evidencia')
p('La fusión convexa α = 0,85 es la referencia de relevancia más sólida en estas corridas. El respaldo mantiene disponibilidad cuando falla o se retrasa el reranker. El reranking completo no aporta una mejora de relevancia demostrada y añade costo temporal; el hedging tampoco ofrece un beneficio consistente entre montajes. La selección por margen es una alternativa para estudiar, pero aún requiere validación de latencia y una comparación controlada TREC-COVID en ds001.')
p('Archivos de auditoría: 04_tablas_y_auditoria/latencia_por_repeticion.csv, latencia_mediana_y_rango.csv, fitness_por_repeticion.csv, pareamiento_hedging.csv, verificacion_summaries.csv e inventario_series.json. El paquete incluye los códigos originales y el código de consolidación para reproducir estas tablas.')


NEW=OUT/'05_trabajo3_khipu_trec'
newmeta=json.loads((NEW/'results_trec_covid_carga_fija_v4/run_meta.json').read_text())
plan=json.loads((NEW/'fixed_load_plan.json').read_text())
analysis=json.loads((NEW/'analysis_summary.json').read_text())
accounting=pd.read_csv(NEW/'slurm_accounting.txt',sep='|',dtype=str)
actual_elapsed=accounting.loc[accounting.JobID==str(newmeta['slurm_job_id']),'Elapsed'].iloc[0]
assert analysis['passed'] and plan['capacity_validated'] is False and plan['trec_capacity_qps'] is None
nf=fitness[fitness.series=='trec-covid_khipu']
old=pages.copy()
for i,(kind,value) in enumerate(old[0][1]):
    if kind=='table' and value[0][0]=='Trabajo':
        value[1][2]=['3','TREC-COVID: intento v4 y ensayo complementario a carga fija','Khipu ds001 · RTX A6000 compartida']
        value[1][3]=['Series adicionales','FiQA y TREC-COVID · dos series completas','Kaggle · Tesla T4']
    if kind=='p' and value.startswith('La serie FiQA/Kaggle'):
        old[0][1][i]=('p','La nueva ejecución de TREC en ds001 conserva el código y entorno de FiQA. El intento de capacidad v4 falla en el primer escalón; se conserva como resultado. Un ensayo complementario mide las mismas cargas absolutas de FiQA, sin declarar una capacidad propia de TREC. Las series Kaggle permanecen separadas.')
    if kind=='table' and value[0][0]=='Pregunta':
        value[1][1][1]=f'FiQA/Khipu y las series Kaggle cumplen en 3/3; TREC/Khipu a carga fija en {int(nf.fitness_i.sum())}/3. No se validó C de TREC.'
        value[1][2][1]=f'Las series previas alcanzan 100 % en F1/F2; el mínimo de TREC/Khipu es {f(nf.worst_F1F2_continuity_pct.min(),2)} %. F6 devuelve error controlado.'
        value[1][3][1]=f'FiQA/Khipu cumple en 3/3; TREC/Khipu a carga fija en {int(nf.fitness_iv.sum())}/3. TREC/Kaggle supera 10 % en dos repeticiones L25.'

pages=[]
page('Diseño experimental y lectura de las estadísticas')
p('El proyecto estudia relevancia, latencia y continuidad. La fusión es f=(1−α)×BM25 normalizado + α×semántico normalizado; α=0,85 da 85 % al puntaje semántico. Los trabajos comparten pipeline, pero responden preguntas distintas: una respuesta rápida o continua no demuestra que contenga mejores documentos. Los complementarios exploran decisiones nuevas de fusión e invocación sin medir sus latencias.')
table(['Pregunta','Diseño y unidad de análisis','Resultado'],[
 ['¿Qué documentos devuelve?','Trabajo 1 · consultas test con qrels; α se fija solo en dev','P@3, nDCG@3, MRR@10 y Recall@20'],
 ['¿Qué pasa al aumentar carga?','Trabajos 2 y 3 · Poisson open-loop, latencia desde instante programado','p50/p95/p99, continuidad y rutas'],
 ['¿Qué ocurre ante fallas?','Errores y demoras inyectados en 13 condiciones','Tres resultados dentro de 2500 ms'],
 ['¿Ayuda duplicar solicitudes?','F3H/F3NH con consultas, llegadas y asignación de demoras iguales','Diferencia de p99 y costo de copias'],
 ['¿Conviene otra decisión?','Complementarios · candidatos y rankings guardados','Relevancia e invocaciones simuladas']],[130,215,157])
h('Controles compartidos en Khipu')
p('FiQA job 63828 y TREC job '+str(newmeta['slurm_job_id'])+' usan el mismo script v4, α = 0,85, Python 3.11.11, las versiones registradas de las siete librerías principales, ds001/A6000, un shard, 4 CPU/hilos y 32 GB. Se mantienen las 13 condiciones, tres repeticiones, 180 segundos por condición, descarte de 30 segundos, plazos y limitador de copias. El código y esos controles se verifican automáticamente.')
h('Cambios intencionales y protocolo que no pudo completarse')
p('Cambian corpus y consultas: FiQA 57.638 documentos/648 consultas test; TREC 171.332/50. Se intentó la misma calibración: 500 solicitudes a 1 QPS, p95 de rerank como umbral y rampa 1–64 QPS en escalones de 120 s. La fuente de calibración v4 es train de FiQA y títulos de TREC con semilla 42. El intento TREC no sostuvo ≥99 % de ruta completa en el primer escalón; por la regla original no tiene C validada en esta grilla.')
p('El ensayo posterior es complementario a carga fija: usa los 2/4/6/8 QPS ya definidos por FiQA, con el umbral propio de TREC. Las etiquetas L25–L100 son porcentajes de la referencia externa de 8 QPS; en TREC no equivalen a porcentajes de una capacidad validada. Así se contrasta la operación a iguales QPS absolutos sin modificar el criterio original.')
h('Denominadores, incertidumbre y límites')
p('p99 se calcula sobre respuestas de tres documentos. Continuidad divide respuestas válidas en ≤2500 ms entre todas las solicitudes medidas. Copias divide duplicadas por invocaciones originales del reranker. Una continuidad alta puede coexistir con respaldos. La mediana y rango de tres repeticiones son descriptivos, no IC; los IC de relevancia remuestrean consultas de forma pareada.')
p('La GPU compartida puede tener distinta contención: mismo nodo no elimina ese factor. Las réplicas comparten máquina y GPU; las fallas son inyectadas. La revisión física de MiniLM de la referencia no quedó registrada y no puede comprobarse retrospectivamente. Las condiciones se ejecutan en orden fijo; el pareamiento de entradas no elimina cambios de contención entre ventanas. Tampoco se midió relevancia por solicitud bajo carga.')
design=pages[0]

pages=[]
page('Trabajo 3 TREC COVID en ds001: dos resultados distintos')
p('El piloto 63909 pasó en 3 min 51 s con modelos reales y ocho condiciones de rutas. Su corpus reducido y calibración diagnóstica solo validan el funcionamiento. El intento de capacidad 63911 usa corpus completo y protocolo v4; el ensayo '+str(newmeta['slurm_job_id'])+' conserva ese pipeline y mide cargas absolutas fijas. Su tiempo real fue '+actual_elapsed+'. Los tres registros se mantienen separados.')
h('1. Intento v4: no se pudo fijar capacidad')
raw=[json.loads(x) for x in (NEW/'results_trec_covid_completo_v4/requests_trec-covid_calib_1qps.jsonl').read_text().splitlines()]
nr=sum(r['route']=='reranked' for r in raw); nl=sum('lex' in r.get('timeouts',[]) for r in raw)
p(f'En las 500 solicitudes iniciales, {nr} ({f(100*nr/len(raw),1)} %) completan reranking y {nl} vencen el plazo léxico de 50 ms. El umbral propio de hedging es {f(plan["hedge_threshold_ms"],3)} ms. En la rampa, el primer escalón entrega aproximadamente 97 % por la ruta completa, por debajo de 99 %. El programa se detiene según su regla, sin emitir una C válida. Esto no demuestra que la capacidad sea cero ni identifica una tasa sostenible menor que 1 QPS.')
p('Los 500 registros se conservan completos. El código original aborta antes de guardar calibration.json y las solicitudes de la rampa; sus resultados solo están disponibles redondeados en el log. No se cambia el plazo, no se rebaja el 99 % y no se sustituye capacidad por continuidad mediante respaldo.')
h('2. Ensayo complementario a iguales QPS que FiQA')
rows=[]
for cond in ['L25','L50','L75','L100','NORERANK','F1','F2']:
    r=l('trec-covid_khipu',cond)
    qps=pd.read_csv(NEW/'results_trec_covid_carga_fija_v4/summary.csv').query('condition == @cond').offered_qps.iloc[0]
    rows.append([cond,f(qps,1),range_ms(r),f(r.continuity_pct_min,2)+' %'])
table(['Condición','QPS nominales','p99 mediana [rango] ms','Continuidad mínima'],rows,[65,105,220,112])
F=l('fiqa_khipu','L100'); R=l('trec-covid_khipu','L100')
p(f'A 8 QPS, FiQA tiene p99 mediano de {f(F.p99_ms_median,1)} ms y TREC {f(R.p99_ms_median,1)} ms. Es un contraste a igual tasa absoluta y montaje nominal, no a iguales porcentajes de capacidad propia ni una atribución causal exclusiva al dataset. El campo C_qps=8 del adaptador solo escala la carga; capacity_validated=false y trec_capacity_qps=null lo aclaran.')
H=reps[(reps.series=='trec-covid_khipu')&reps.condition.isin(['F3H','F3NH'])].pivot(index='rep',columns='condition',values='p99_ms')
exposure=pd.read_csv(NEW/'hedging_pareado.csv')
p('La reducción p99 sin hedge menos con hedge es '+', '.join(f(x,1) for x in H.F3NH-H.F3H)+' ms por repetición. Consultas, llegadas y asignación de demoras coinciden, pero las demoras efectivas difieren en '+', '.join(str(int(x)) for x in exposure.observed_delay_mismatches_postwarm)+' solicitudes poscalentamiento por repetición al activarse respaldo antes del reranker. La diferencia de p99 no aísla solo el hedge. Fitness temporales bajo estas cargas: (i) '+str(int(nf.fitness_i.sum()))+'/3; (iii) '+str(int(nf.fitness_iii.sum()))+'/3; (iv) '+str(int(nf.fitness_iv.sum()))+'/3. No certifican la capacidad v4 que no pudo calibrarse.')
p('Fuentes: 05_trabajo3_khipu_trec/, intento original, fixed_load_plan.json, los 39 archivos del ensayo, notebook ejecutado, nueve figuras, verificación y logs Slurm. La contención compartida limita todas las inferencias entre corridas.')
trecpage=pages[0]

title,blocks=old[3]
for i,(kind,value) in enumerate(blocks):
    if kind=='h' and value=='Comparación que todavía falta': blocks[i]=('h','Cómo se relaciona con el ensayo nuevo de Khipu')
    if kind=='p' and value.startswith('TREC-COVID aún no tiene'):
        blocks[i]=('p','La ejecución nueva en ds001 permite contrastar TREC con FiQA a iguales QPS absolutos. Su intento de capacidad falla y se documenta por separado. Kaggle conserva dos series propias completas; sigue siendo incorrecto mezclar sus latencias con Khipu como si solo cambiara el dataset.')
old[3]=('Series de Kaggle como evidencia complementaria',blocks)
title,blocks=old[5]
for i,(kind,value) in enumerate(blocks):
    if kind=='p' and value.startswith('Se revisaron 117 filas'):
        blocks[i]=('p',value.replace('117','156').replace('Los nueve pares F3H/F3NH tienen idénticas consultas, llegadas y banderas de demora.', 'Los doce pares F3H/F3NH tienen idénticas consultas y llegadas. Las banderas de demora de las nueve parejas originales coinciden; en TREC/Khipu se registran diferencias de exposición por respaldos previos al reranker.'))
    if kind=='h' and value=='Qué debe correr el compañero en ds001': blocks[i]=('h','Ejecución nueva, trazabilidad y límites')
    if kind=='p' and value.startswith('<b>Trabajo 3 de latencia'):
        blocks[i]=('p','El intento 63911 conserva el protocolo de capacidad y su fallo. El job '+str(newmeta['slurm_job_id'])+' ejecuta un ensayo complementario a las cargas absolutas de FiQA, con código idéntico. Los 39 resúmenes se contrastan con las solicitudes y el notebook contiene '+str(analysis['notebook_code_cells'])+' celdas ejecutadas, nueve figuras y cero errores.')
    if kind=='p' and value.startswith('Usar todas las 13 condiciones'):
        blocks[i]=('p','comparability_final.json distingue controles verificados y límites: código, α, entorno, recursos, condiciones y cargas coinciden; la capacidad de TREC no fue validada. No se certifica idéntica contención ni revisión física de MiniLM de la referencia. Los scripts de análisis se separan del benchmark congelado y todos los artefactos se inventarían con SHA-256.')
    if kind=='p' and value.startswith('La fusión convexa α = 0,85 es la referencia'):
        blocks[i]=('p','La fusión α = 0,85 sigue siendo la referencia de relevancia más sólida entre las variantes evaluadas. Los respaldos protegen continuidad y se deben leer junto con las proporciones de ruta. El intento fallido de calibración revela un límite operativo del protocolo en TREC, mientras el ensayo fijo describe su comportamiento a las cargas de FiQA. La selección por margen aún necesita una prueba temporal propia.')
old[5]=('Auditoría y trazabilidad de la comparación',blocks)
pages=[old[0],design,old[1],old[2],trecpage,old[3],old[4],old[5]]

# Editable source with the same content as the PDF.
md=[]
for title,blocks in pages:
    md += ['# '+title,'']
    for kind,value in blocks:
        if kind=='p': md += [value.replace('<b>','**').replace('</b>','**'),'']
        elif kind=='h': md += ['## '+value,'']
        else:
            headers,rows,_=value
            md += ['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|']
            md += ['| '+' | '.join(str(x) for x in row)+' |' for row in rows]
            md += ['']
(DOC/'Resumen_MINION_Trabajos_1_2_3.md').write_text('\n'.join(md),encoding='utf-8')

font=Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Arial',str(font/'arial.ttf')))
pdfmetrics.registerFont(TTFont('ArialBold',str(font/'arialbd.ttf')))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='ArialBold',italic='Arial',boldItalic='ArialBold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyReport',fontName='Arial',fontSize=9.4,leading=13,spaceAfter=7,textColor=colors.HexColor('#20252B')))
styles.add(ParagraphStyle(name='TitleReport',fontName='ArialBold',fontSize=21,leading=25,spaceAfter=14,textColor=colors.black))
styles.add(ParagraphStyle(name='HeadingReport',fontName='ArialBold',fontSize=11.2,leading=15,spaceBefore=7,spaceAfter=6,keepWithNext=True,textColor=colors.black))
styles.add(ParagraphStyle(name='CellReport',fontName='Arial',fontSize=8.1,leading=10.7,spaceAfter=0))
styles.add(ParagraphStyle(name='CellHead',fontName='ArialBold',fontSize=8.1,leading=10.7,textColor=colors.white))
story=[]
for i,(title,blocks) in enumerate(pages):
    if i: story.append(PageBreak())
    story.append(Paragraph(title,styles['TitleReport']))
    for kind,value in blocks:
        if kind=='p': story.append(Paragraph(value,styles['BodyReport']))
        elif kind=='h': story.append(Paragraph(value,styles['HeadingReport']))
        else:
            headers,rows,widths=value
            data=[[Paragraph(html.escape(str(x)),styles['CellHead']) for x in headers]]
            data += [[Paragraph(html.escape(str(x)),styles['CellReport']) for x in row] for row in rows]
            t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#263746')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F1F4F7'),colors.white]),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
                ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#263746'))]))
            story.extend([t,Spacer(1,8)])
def footer(canvas,doc):
    canvas.setFont('Arial',8); canvas.setFillColor(colors.HexColor('#66717D'))
    canvas.drawString(46,25,'MINION · síntesis de evidencia experimental · 18 noviembre 2026')
    canvas.drawRightString(A4[0]-46,25,str(doc.page))
pdf=DOC/'Resumen_MINION_Trabajos_1_2_3.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=40,bottomMargin=42,
    title='Resumen integrado de los tres trabajos MINION',author='Equipo MINION')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
readme='''# MINION integrated evidence

Start with `00_resumen/Resumen_MINION_Trabajos_1_2_3.pdf` (Spanish report) or its editable Markdown source.

- `01_trabajo1/ajuste_dev/`: validated alpha=0.85, development sweep and Slurm evidence.
- `01_trabajo1/relevancia_test/`: executed notebook, figures, raw candidate scores, relevance metrics and paired bootstrap.
- `01_trabajo1/complementarios/`: CPU job 63778, RRF and selective reranking analyses, thresholds and seeds.
- `02_trabajo2_khipu_fiqa/`: original branch `paper/trabajo2`, including pilots and final `results_fiqa_completo_v4/`.
- `03_trabajos2y3_kaggle/`: original branch `feat/khipu-kaggle-results`, FiQA and TREC-COVID Kaggle results and executed notebooks.
- `04_tablas_y_auditoria/`: independently checked request-level summaries, medians/ranges, fitness and provenance.
- `05_trabajo3_khipu_trec/`: pilot, failed capacity attempt, complementary fixed-load run, code, logs, notebook, figures and verification.

The original sources are preserved. Khipu and Kaggle latency series remain separate. Pilots are historical evidence, not final results.
The new `05_trabajo3_khipu_trec/` preserves failed capacity attempt 63911 and a complementary fixed-load run at the same absolute QPS as FiQA. `C_qps=8` in its adapter is an external load scale, NOT a validated TREC capacity. See the Spanish experimental plan and final comparability checks.
`procedencia.json` pins the reviewed branch commits. `MANIFEST_SHA256.json` inventories this package.
No repository branch was changed by this local consolidation. The new TREC benchmark was executed through Slurm on ds001. Original branch sources remain unchanged; the new run and analysis are in folder 05.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
shutil.copy2(__file__,T/'resumen_minion.py'); shutil.copy2(ROOT/'work/consolidar_minion.py',T/'consolidar_minion.py')
print(pdf)
