import { useEffect, useMemo, useState } from 'react'
import Aurora from './components/rb/Aurora'
import BlurText from './components/rb/BlurText'
import ShinyText from './components/rb/ShinyText'
import SpotlightCard from './components/rb/SpotlightCard'
type Method='semantic'|'fusion'|'llm'
type Scores={P3:number;nDCG3:number;MRR10:number}
type Item={id:string;query:string;gain:number;llmGain:number;hit:boolean}
type Meta={queries:number;documents:number;hardware:string;index:Item[];quality:Record<string,Record<string,string>>;latency:Record<string,Record<string,string>>;ci:Record<string,string>[];originalLLMMedianMs:number;llmLatencyN:number}
type Doc={id:string;title:string;text:string;rel:number|null;sem:number|null;fus:number|null;llm:number|null;lexNorm:number|null;semNorm:number|null}
type Query={id:string;query:string;cands:Doc[];rankS:string[];rankA:string[];rankB:string[];metrics:Record<Method,Scores>;poolSize:number}
const methods:Method[]=['semantic','fusion','llm'],names={semantic:'Solo semántica',fusion:'Fusión convexa',llm:'LLM · Qwen'},sk={semantic:'sem',fusion:'fus',llm:'llm'} as const
const format=(n:number,d=3)=>n.toLocaleString('es-PE',{minimumFractionDigits:d,maximumFractionDigits:d})

const auroraColors = ['#5eead4', '#6366f1', '#a855f7']
const methodLights = { semantic: '#93c5fd', fusion: '#5eead4', llm: '#a855f7' }

function fusionWins(query: Item) {
  return Number(query.gain > 0) + Number(query.llmGain < 0)
}

function compareQueries(a: Item, b: Item) {
  return fusionWins(b) - fusionWins(a)
    || Math.min(b.gain, -b.llmGain) - Math.min(a.gain, -a.llmGain)
    || (b.gain - b.llmGain) - (a.gain - a.llmGain)
    || a.id.localeCompare(b.id, 'en', { numeric: true })
}

function winLabel(query: Item) {
  if (fusionWins(query) === 2) return 'Gana a ambos'
  if (query.gain > 0) return 'Supera a semántica'
  if (query.llmGain < 0) return 'Supera a Qwen'
  return ''
}

const queryGroups = ['Otras consultas', 'Fusión supera a un método', 'Fusión gana a ambos']

function Hero({ onNavigate }: { onNavigate: (tab: string) => void }) {
  return (
    <section className="demo-hero">
      <div className="hero-aurora" aria-hidden="true">
        <Aurora colorStops={auroraColors} amplitude={1.1} speed={0.6} dpr={1} />
      </div>
      <div className="hero-copy">
        <h1 aria-label="MINION">
          <BlurText text="MINION" animateBy="letters" trigger="load" delay={70} className="justify-center" />
        </h1>
        <ShinyText text="Recuperación y ranking de evidencia" color="#cbd5e1" shineColor="#ffffff" speed={3} />
        <p>Compara cómo la búsqueda semántica, la fusión convexa y Qwen ordenan los resultados para la misma pregunta.</p>
        <div className="hero-actions">
          <button className="primary" onClick={() => onNavigate('explore')}>Ver comparador</button>
          <button onClick={() => onNavigate('results')}>Resultados medidos</button>
        </div>
      </div>
    </section>
  )
}
function Judgment({rel}:{rel:number|null}){return <span className={'judgment '+(rel===null?'unknown':rel>0?'positive':'negative')}>{rel===null?'Sin juicio':rel===2?'Muy relevante · 2':rel>0?'Relevante · 1':'No relevante · 0'}</span>}
function Highlight({text,query}:{text:string;query:string}){const terms=query.match(/[a-zA-Z]{4,}/g)?.filter(x=>!['what','which','with','that','this','from','does','have','would','should','about','there'].includes(x.toLowerCase()))??[];if(!terms.length)return <>{text}</>;return <>{text.split(new RegExp(`(${[...new Set(terms)].join('|')})`,'gi')).map((x,i)=>i%2?<mark key={i}>{x}</mark>:x)}</>}
export default function PaperApp(){
 const [manifest,setManifest]=useState<Record<string,Meta>|null>(null),[ds,setDs]=useState('trec'),[tab,setTab]=useState('explore'),[id,setId]=useState(''),[query,setQuery]=useState<Query|null>(null),[filter,setFilter]=useState(''),[error,setError]=useState('')
 const [selected,setSelected]=useState<Doc|null>(null),[visible,setVisible]=useState(3),[running,setRunning]=useState(false),[scenario,setScenario]=useState('normal'),[flow,setFlow]=useState(false)
 useEffect(()=>{fetch('/paperdata/manifest.json').then(r=>{if(!r.ok)throw Error('No se pudieron cargar los datos');return r.json()}).then(setManifest).catch(e=>setError(e.message))},[])
 const meta=manifest?.[ds]
 const orderedQueries = useMemo(() => [...(meta?.index ?? [])].sort(compareQueries), [meta])
 useEffect(() => {
   setId(orderedQueries[0]?.id ?? '')
   setQuery(null)
   setFilter('')
   setSelected(null)
 }, [orderedQueries])
 useEffect(()=>{if(!id||!meta)return;const a=new AbortController();setError('');setQuery(null);setRunning(false);setVisible(3);fetch(`/paperdata/${ds}/q/${id}.json`,{signal:a.signal}).then(r=>{if(!r.ok)throw Error('Consulta no disponible');return r.json()}).then(setQuery).catch(e=>{if(e.name!=='AbortError')setError(e.message)});return()=>a.abort()},[id,ds,meta])
 useEffect(()=>{if(!running)return;setVisible(0);let step=0;const t=setInterval(()=>{step++;setVisible(step);if(step===3)setRunning(false)},650);return()=>clearInterval(t)},[running])
 useEffect(()=>{if(!flow)return;const t=setTimeout(()=>setFlow(false),1800);return()=>clearTimeout(t)},[flow])
 useEffect(()=>{const h=(e:KeyboardEvent)=>{if(e.key==='Escape')setSelected(null)};window.addEventListener('keydown',h);return()=>window.removeEventListener('keydown',h)},[])
 const search = filter.trim().toLowerCase()
 const list = orderedQueries.filter(item => item.query.toLowerCase().includes(search) || item.id.includes(search))
 const selectedQuery = orderedQueries.find(item => item.id === id)
 const navigate = (target: string) => {
   setTab(target)
   document.getElementById('experiment')?.scrollIntoView()
 }
 const docs=useMemo(()=>Object.fromEntries((query?.cands??[]).map(x=>[x.id,x])),[query])
 const ranks:Record<Method,string[]>={semantic:query?.rankS??[],fusion:query?.rankA??[],llm:query?.rankB??[]}
 const pick = (kind: 'fusion' | 'llm') => {
   const examples = kind === 'fusion' ? orderedQueries : [...orderedQueries].sort((a, b) => b.llmGain - a.llmGain)
   if (!examples.length) return
   setFilter('')
   setId(examples[0].id)
   if (kind === 'fusion') document.querySelector('.query-list')?.scrollTo({ top: 0 })
 }
 const time=(m:Method)=>meta?(m==='llm'?meta.originalLLMMedianMs:Number(meta.latency[m==='semantic'?'semantic':'fusion_matched'].p50_seconds)*1000):0
 if(!manifest)return <div className="boot"><span className="logo">M</span><h1>{error||'Preparando la evidencia…'}</h1>{error&&<button onClick={()=>location.reload()}>Reintentar</button>}</div>
 return <div className="paper-app"><header className="topbar"><a className="brand" href="#"><span className="logo">M</span><span>MINION<small>EVIDENCE LAB</small></span></a><nav>{[['explore','Explorar rankings'],['results','Evidencia experimental'],['resilience','MiniLM y resiliencia']].map(([k,t])=><button key={k} className={tab===k?'active':''} onClick={()=>setTab(k)}>{t}</button>)}</nav><span className="recorded"><i/> Resultados reales · reproducción visual</span></header>
 <Hero onNavigate={navigate} />
 <main id="experiment"><section className="intro"><div><h2>{tab==='explore'?'Comparar los top 3':tab==='results'?'Resultados medidos':'MiniLM y resiliencia'}</h2><p>10.000 registros · {meta?.queries} consultas del benchmark</p></div><div className="dataset"><small>COLECCIÓN</small><div>{[['trec','TREC-COVID'],['fiqa','FiQA']].map(([k,t])=><button key={k} className={ds===k?'selected':''} aria-pressed={ds===k} onClick={()=>setDs(k)}>{t}</button>)}</div></div></section>
 <section className="headline"><div><span>Fusión vs. solo semántica</span><strong>{ds==='trec'?'+7,33 pp':'Empate en P@3'}</strong><small>{ds==='trec'?'P@3 · IC 95 %: +3,33 a +11,33 pp':'MRR@10 mejora +0,0080 · IC positivo'}</small></div><div><span>Coste adicional de la fusión</span><strong>+{ds==='trec'?'6,15':'5,21'} <em>ms</em></strong><small>Media · control medido en el mismo job</small></div><div><span>Lo que muestran los datos</span><strong className="statement">Más complejidad ≠ mejor ranking</strong><small>Qwen y MiniLM no demostraron mejora sobre la fusión</small></div></section>
 {tab==='explore'&&<section className="workspace">
   <aside className="queries">
     <div className="panel-heading"><h2>Preguntas del benchmark</h2><span>{meta?.queries}</span></div>
     <input aria-label="Buscar consulta" placeholder="Buscar palabra o ID…" value={filter} onChange={e=>setFilter(e.target.value)} />
     <div className="quick">
       <button onClick={()=>pick('fusion')}>Mejor caso de fusión</button>
       <button onClick={()=>pick('llm')}>Mejor caso del LLM</button>
       <button onClick={()=>meta&&setId(meta.index[Math.floor(Math.random()*meta.index.length)].id)}>Aleatoria</button>
     </div>
     <p className="list-note">Primero las victorias en P@3. Los promedios incluyen todas las consultas.</p>
     <div className="query-list" key={ds}>
       {list.length === 0 && <p>No hay coincidencias.</p>}
       {[2, 1, 0].map(wins => {
         const group = list.filter(item => fusionWins(item) === wins)
         return group.length > 0 && (
           <div key={wins} data-fusion-wins={wins}>
             <h3>{queryGroups[wins]} <span>{group.length}</span></h3>
             {group.map(item => (
               <button key={item.id} data-query-id={item.id} className={id===item.id?'current':''}
                 aria-current={id === item.id} onClick={() => setId(item.id)}>
                 <small>Q{item.id}{winLabel(item) && <span className="win-label">{winLabel(item)}</span>}</small>
                 {item.query}
               </button>
             ))}
           </div>
         )
       })}
     </div>
   </aside>
 <div>{error?<div className="surface">{error}</div>:!query?<div className="surface">Cargando consulta…</div>:<>
   <SpotlightCard className="query-banner" spotlightColor={auroraColors[0]}>
     <div>
       <span className="eyebrow">CONSULTA REAL · Q{query.id}</span>
       <h2>{query.query}</h2>
       {selectedQuery && fusionWins(selectedQuery) > 0 && <div className="query-win">Fusión {winLabel(selectedQuery).toLowerCase()} en P@3</div>}
     </div>
     <button className="primary" disabled={running} onClick={()=>setRunning(true)}>{running?'Reproduciendo…':'▶ Reproducir recorrido'}</button>
   </SpotlightCard>
   <div className="pipeline">
     <div className="parallel-stages">
       <span><strong>BM25</strong> · top 10 léxico</span>
       <span><strong>BGE</strong> · top 10 semántico</span>
     </div>
     <b aria-hidden="true">→</b>
     <span className="pool-stage"><strong>Unión por ID</strong> · {query.poolSize} candidatos</span>
     <b aria-hidden="true">→</b>
     <span className="rank-stage"><strong>Fusión o Qwen</strong> · top 3</span>
     <small>El baseline usa el top 10 de BGE.<br/>Recorrido animado de resultados guardados.</small>
   </div>
 <div className="columns">{methods.map((m,mi)=><SpotlightCard key={m} className={`ranking ${m}`} spotlightColor={methodLights[m]}><div className="method-title"><div><h3>{names[m]}</h3><small>{m==='semantic'?'El punto de partida':m==='fusion'?'Palabras + significado':'Un miniprompt por documento'}</small></div></div><div className="method-stat"><div><small>P@3 de esta consulta</small><strong>{format(query.metrics[m].P3*100,1)}<em>%</em></strong></div><div><small>p50 del estudio</small><b>{format(time(m),time(m)<100?1:0)} ms</b></div></div><div className="progress"><i style={{width:visible>mi?'100%':'12%'}}/></div><div className={`cards ${visible>mi?'visible':''}`}>{ranks[m].slice(0,3).map((docid,pos)=>{const d=docs[docid];if(!d)return null;const score=d[sk[m]],prev=query.rankS.indexOf(docid),delta=prev-pos;return <button key={docid} className="doc-card" onClick={()=>setSelected(d)}><div className="card-top"><span className="rank">{pos+1}</span><Judgment rel={d.rel}/><span className="movement">{m==='semantic'?'BASE':prev<0?'NUEVO':delta===0?'=':delta>0?'↑ '+delta:'↓ '+Math.abs(delta)}</span></div><h4>{d.title}</h4><p><Highlight text={d.text.slice(0,220)} query={query.query}/>{d.text.length>220?'…':''}</p><div className="score-line"><span>{m==='semantic'?'Similitud':'Score de ranking'}</span><b>{score===null?'—':format(score,4)}</b></div><div className="score-bar"><i style={{width:Math.max(0,Math.min(1,score??0))*100+'%'}}/></div><small className="inspect">Inspeccionar documento ↗</small></button>})}</div><div className="column-foot">nDCG@3 <b>{format(query.metrics[m].nDCG3)}</b><span>MRR@10 <b>{format(query.metrics[m].MRR10)}</b></span></div></SpotlightCard>)}</div><div className="reading"><strong>Cómo leerlo</strong><span>La barra representa el score de ese método, <b>no una probabilidad</b>. Los juicios oficiales son independientes. “Sin juicio” no significa “irrelevante”.</span><span>↑ ↓ Cambio de posición respecto al baseline semántico.</span></div></>}</div></section>}
 {tab==='results'&&meta&&<section><div className="section-title"><div className="eyebrow">LO QUE PODEMOS AFIRMAR</div><h2>La comparación completa, sin elegir solo los aciertos.</h2><p>{meta.queries} consultas · {meta.hardware}</p></div><div className="evidence-grid"><article className="surface"><h3>Relevancia global</h3><table><thead><tr><th>Método</th><th>P@3</th><th>nDCG@3</th><th>MRR@10</th></tr></thead><tbody>{methods.map(m=><tr key={m}><th>{names[m]}</th>{['P3','nDCG3','MRR10'].map(k=><td key={k}>{format(Number(meta.quality[m==='fusion'?'fusion_reference':m==='llm'?'LLM_reference':'semantic'][k]),4)}</td>)}</tr>)}</tbody></table><p className="muted">Fusión y Qwen: corrida original. Baseline: nueva corrida. El control de fusión re-medido se conserva por separado.</p><h3>Fusión recalculada − solo semántica</h3>{meta.ci.filter(c=>c.comparison==='fusion_matched minus semantic').map(c=><div key={c.metric} className="ci"><b>{c.metric}</b><span>{format(Number(c.delta),4)}</span><span>IC 95 % [{format(Number(c.ci95_low),4)}; {format(Number(c.ci95_high),4)}]</span><small>{Number(c.ci95_low)>0?'Positivo':'Incluye cero'}</small></div>)}</article><article className="surface"><h3>Latencia · 1.000 solicitudes por método</h3>{['semantic','fusion_matched'].map(m=><div className="latency" key={m}><span>{m==='semantic'?'Solo semántica':'Fusión recalculada'}</span><strong>{format(Number(meta.latency[m].mean_seconds)*1000,2)} ms</strong><div><i style={{width:Number(meta.latency[m].mean_seconds)/.045*100+'%'}}/></div><small>p95 {format(Number(meta.latency[m].p95_seconds)*1000,2)} ms · p99 {format(Number(meta.latency[m].p99_seconds)*1000,2)} ms</small></div>)}<div className="callout">Qwen anterior: p50 <b>{format(meta.originalLLMMedianMs,1)} ms</b> · {meta.llmLatencyN} solicitudes. Otra ventana de ejecución, no se mezcla con este control.</div><p>La fusión suma pocos milisegundos. La mejora de calidad depende del conjunto: es clara en P@3 de TREC; en FiQA hay empate en P@3.</p></article></div><article className="surface"><h3>Qué incluye este experimento</h3><p>10.000 registros, no 10.000 artículos completos. BGE usa hasta 512 tokens; Qwen, hasta 1.024 tokens de entrada en TREC y 384 del documento en FiQA. En FiQA, 251 de 648 consultas conservan positivos juzgados en la muestra. Los scores no están calibrados como probabilidades.</p></article></section>}
 {tab==='resilience'&&<section><div className="section-title"><div className="eyebrow">ESTUDIO COMPLEMENTARIO · CORPUS COMPLETOS</div><h2>¿Y si añadimos un reranker después de la fusión?</h2><p>Esta arquitectura se ejecutó con MiniLM, un cross-encoder. No es Qwen ni comparte los candidatos de las muestras de 10.000 documentos.</p></div><article className="surface"><div className="scenarios"><span>Explorar una ruta:</span>{[['normal','Normal'],['failure','Reranker falla'],['slow','Réplica A lenta']].map(([k,t])=><button key={k} className={scenario===k?'selected':''} onClick={()=>setScenario(k)}>{t}</button>)}<button className="primary" onClick={()=>setFlow(true)}>{flow?'Recorriendo…':'▶ Mostrar recorrido'}</button></div><div className={'flow '+(flow?'animate':'')}><div>BM25 ∥ BGE<small>Unión de candidatos</small></div><span>→</span><div className="green">Fusión convexa<small>Ranking disponible</small></div><span>→</span><div className={scenario==='failure'?'failed':''}>MiniLM A<small>{scenario==='failure'?'Error controlado':scenario==='slow'?'Supera umbral de espera':'Responde a tiempo'}</small></div><span>→</span><div>Top 3<small>{scenario==='failure'?'De la fusión · fallback':scenario==='slow'?'Primera réplica válida':'Del ranking MiniLM'}</small></div></div><div className="callout"><b>{scenario==='failure'?'↳ Fallback: conservar el ranking fusionado':scenario==='slow'?'↳ Hedging: invocar MiniLM B':'↳ Ruta normal: MiniLM determina el orden'}</b><p>{scenario==='failure'?'Si falla el reranker o vence su plazo, se devuelve el top 3 de la fusión. Responder no implica mejorar la relevancia.':scenario==='slow'?'Una segunda réplica lógica recibe la solicitud. Se toma la primera respuesta válida. Ambas réplicas compartían GPU, no eran servidores independientes.':'La fusión produce una primera ordenación. MiniLM evalúa los mismos candidatos y los ordena nuevamente.'}</p></div><p className="muted">Animación explicativa de rutas ensayadas. No ejecuta MiniLM ni inyecta fallas reales.</p></article><div className="evidence-grid"><article className="surface"><h3>¿Mejoró la calidad con MiniLM?</h3><table><thead><tr><th>Corpus completo</th><th>Fusión P@3</th><th>MiniLM P@3</th></tr></thead><tbody><tr><th>FiQA · 57.638 documentos</th><td>0,2515</td><td>0,2310</td></tr><tr><th>TREC · 171.332 documentos</th><td>0,9133</td><td>0,8867</td></tr></tbody></table><p>FiQA: intervalo negativo. TREC: incluye cero. No se demostró una mejora al añadir MiniLM.</p></article><article className="surface"><h3>Respaldo y hedging: otra pregunta</h3><p>En Kaggle, el respaldo mantuvo tres resultados dentro de 2,5 s en las ventanas F1/F2. El hedging redujo p99 bajo demoras inyectadas, pero TREC superó el límite de duplicadas: <b>10,1124 %</b>.</p><p>En Khipu el beneficio no fue consistente. Estos resultados no demuestran mejora de relevancia ni disponibilidad de producción.</p></article></div></section>}
 <footer><span>MINION · evidencia experimental, no superioridad universal.</span><span>Scores guardados · sin inferencia en vivo · paper y experimentos reales</span></footer></main>
 {selected&&query&&<div className="backdrop" onClick={()=>setSelected(null)}><section className="modal" role="dialog" aria-modal="true" aria-label="Detalle del documento" onClick={e=>e.stopPropagation()}><button className="close" aria-label="Cerrar documento" onClick={()=>setSelected(null)}>×</button><span className="eyebrow">DOCUMENTO {selected.id}</span><h2>{selected.title}</h2><Judgment rel={selected.rel}/><div className="signals">{[['Léxico normalizado',selected.lexNorm,'× 0,15'],['Semántico normalizado',selected.semNorm,'× 0,85'],['Score de fusión',selected.fus,'No es una probabilidad']].map(([label,value,note])=><div key={String(label)}><span>{label}</span><b>{value===null?'—':format(Number(value),4)}</b><small>{note}</small></div>)}</div><p className="doc-text"><Highlight text={selected.text} query={query.query}/></p><small className="muted">Extracto de hasta 2.400 caracteres. El resaltado literal de términos es orientativo, no una explicación causal del modelo. BGE y Qwen tienen límites de tokens documentados.</small></section></div>}
 </div>
}
