"""Build an honest report: failed capacity attempt + complementary fixed-load run."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
base=(ROOT/'work/resumen_minion.py').read_text(encoding='utf-8')
extension=r'''
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
'''
base=base.replace('# Editable source with the same content as the PDF.',extension+'\n# Editable source with the same content as the PDF.')
base=base.replace('There is no TREC-COVID latency run on Khipu ds001 in the reviewed branches; this is the required follow-up for a controlled Khipu comparison.',
 'The new `05_trabajo3_khipu_trec/` preserves failed capacity attempt 63911 and a complementary fixed-load run at the same absolute QPS as FiQA. `C_qps=8` in its adapter is an external load scale, NOT a validated TREC capacity. See the Spanish experimental plan and final comparability checks.')
base=base.replace('No model inference or new latency benchmark was executed.',
 'The new TREC benchmark was executed through Slurm on ds001. Original branch sources remain unchanged; the new run and analysis are in folder 05.')
base=base.replace('- `04_tablas_y_auditoria/`: independently checked request-level summaries, medians/ranges, fitness and provenance.',
 '- `04_tablas_y_auditoria/`: independently checked request-level summaries, medians/ranges, fitness and provenance.\n- `05_trabajo3_khipu_trec/`: pilot, failed capacity attempt, complementary fixed-load run, code, logs, notebook, figures and verification.')
(ROOT/'work/resumen_minion_actualizado.py').write_text(base,encoding='utf-8')
print('FIXED_LOAD_REPORT_BUILDER_PREPARED')
