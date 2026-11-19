import { useEffect, useMemo, useRef, useState } from 'react'
import SpotlightCard from './components/rb/SpotlightCard'
import type { IdxItem, Q, Summary } from './types'

const SPEEDS = [{ l: '0.15×', v: 0.15 }, { l: '0.3×', v: 0.3 }, { l: '1× real', v: 1 }]
const BATCHES = [1, 4, 8]

function Bar({ p, color }: { p: number; color: string }) {
  return <div className="h-1.5 overflow-hidden rounded bg-white/10"><div className="h-full rounded transition-[width] duration-75" style={{ width: `${Math.min(100, p * 100)}%`, background: color }} /></div>
}

function Stage({ name, sub, p, color, ms }: { name: string; sub: string; p: number; color: string; ms?: number }) {
  const state = p >= 1 ? 'done' : p > 0 ? 'run' : 'idle'
  return (
    <div className={`rounded-lg border p-3 transition-colors ${state === 'run' ? 'border-white/40 bg-white/10' : state === 'done' ? 'border-white/15 bg-white/[0.04]' : 'border-white/5 opacity-50'}`}>
      <div className="flex items-center justify-between text-sm"><span className="font-medium">{name}</span>
        <span className="mono text-xs text-slate-400">{state === 'done' && ms != null ? `${ms.toFixed(0)} ms ✓` : state === 'run' ? '…' : ''}</span></div>
      <div className="mb-2 text-xs text-slate-400">{sub}</div><Bar p={p} color={color} />
    </div>
  )
}

export default function Demo({ idx, sum }: { idx: IdxItem[]; sum: Summary | null }) {
  const [onlyHit, setOnlyHit] = useState(true)
  const [filter, setFilter] = useState('')
  const [sel, setSel] = useState<string | null>(null)
  const [q, setQ] = useState<Q | null>(null)
  const [batch, setBatch] = useState(4)
  const [speed, setSpeed] = useState(0.3)
  const [t, setT] = useState(0)          // tiempo virtual (ms)
  const [running, setRunning] = useState(false)
  const raf = useRef(0)

  const list = useMemo(() => idx.filter(i => (!onlyHit || i.hit) && i.query.toLowerCase().includes(filter.toLowerCase())).slice(0, 60), [idx, onlyHit, filter])
  useEffect(() => { if (!sel && list.length) setSel(list[0].id) }, [list, sel])
  useEffect(() => { if (sel) fetch(`/data/q/${sel}.json`).then(r => r.json()).then((d: Q) => { setQ(d); setT(0); setRunning(false) }) }, [sel])

  const bs = sum?.batching
  const factor = bs && bs[String(batch)] ? bs[String(batch)].mean_s / bs['1'].mean_s : 1
  const S = q?.times.search_ms ?? 1, F = Math.max(q?.times.fusion_ms ?? 0.5, 1), L = (q?.times.llm_ms ?? 1) * factor
  const n = q?.cands.length ?? 0, nb = Math.ceil(n / batch)
  const endA = S + F, endB = S + L + F

  useEffect(() => {
    if (!running) return
    let last = performance.now()
    const tick = (now: number) => {
      setT(prev => { const nt = prev + (now - last) * speed; if (nt >= endB + 40) setRunning(false); return Math.min(nt, endB + 40) })
      last = now; raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf.current)
  }, [running, speed, endB])

  const run = () => { setT(0); setRunning(true) }
  const doneA = t >= endA, doneB = t >= endB
  const byId = useMemo(() => Object.fromEntries((q?.cands ?? []).map(c => [c.id, c])), [q])
  const batchOf = (i: number) => Math.floor(i / batch)
  const scored = (i: number) => t >= S + (L * (batchOf(i) + 1)) / nb
  const bmP = Math.min(1, t / (S * 0.4)), bgeP = Math.min(1, t / S)

  const Top = ({ ids, show, label, color }: { ids: string[]; show: boolean; label: string; color: string }) => (
    <div className="space-y-2">
      {ids.slice(0, 5).map((id, r) => { const c = byId[id]; return (
        <div key={id} className={`rounded-lg border border-white/10 bg-black/30 p-3 text-sm transition-all duration-500 ${show ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0'}`} style={{ transitionDelay: `${r * 90}ms` }}>
          <div className="mb-1 flex items-center gap-2"><span className="mono flex h-5 w-5 items-center justify-center rounded text-[11px] font-bold text-slate-900" style={{ background: color }}>{r + 1}</span>
            <span className="mono text-xs text-slate-500">{label} {(label === 'fusión' ? c.fus : c.llm).toFixed(3)}</span>
            {c.rel > 0 && <span className="ml-auto rounded-full bg-emerald-400/15 px-2 py-0.5 text-[11px] text-emerald-300">✓ relevante</span>}</div>
          <p className="line-clamp-2 text-slate-300">{c.text}</p></div>) })}
    </div>)

  return (
    <section id="demo" className="scroll-mt-8">
      <h2 className="text-3xl font-semibold">Flujo en vivo</h2>
      <p className="mt-2 max-w-3xl text-slate-400">Elige una consulta real del benchmark. Ambas arquitecturas comparten recuperación y candidatos; solo cambia cómo se ordenan. Los tiempos son los medidos para esa consulta.</p>
      <div className="mt-6 grid gap-6 lg:grid-cols-[320px_1fr]">
        <SpotlightCard className="h-[560px] overflow-hidden !p-0">
          <div className="space-y-2 border-b border-white/10 p-3">
            <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Buscar consulta…" className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none focus:border-teal-300/60" />
            <label className="flex items-center gap-2 text-xs text-slate-400"><input type="checkbox" checked={onlyHit} onChange={e => setOnlyHit(e.target.checked)} />Solo consultas con respuesta en los candidatos ({idx.filter(i => i.hit).length})</label>
            <button onClick={() => list.length && setSel(list[Math.floor(Math.random() * list.length)].id)} className="text-xs text-teal-300 hover:underline">🎲 Consulta aleatoria</button>
          </div>
          <ul className="h-[455px] overflow-y-auto">{list.map(i => (
            <li key={i.id}><button onClick={() => setSel(i.id)} className={`w-full border-b border-white/5 px-3 py-2.5 text-left text-sm hover:bg-white/5 ${sel === i.id ? 'bg-teal-300/10 text-white' : 'text-slate-300'}`}>
              <span className="line-clamp-2">{i.query}</span></button></li>))}</ul>
        </SpotlightCard>

        <div className="space-y-4">
          <SpotlightCard>
            <div className="flex flex-wrap items-center gap-3">
              <p className="min-w-0 flex-1 text-lg font-medium">“{q?.query ?? '…'}”</p>
              <div className="flex items-center gap-1 text-xs text-slate-400">Lote LLM:
                {BATCHES.map(b => <button key={b} onClick={() => { setBatch(b); setT(0); setRunning(false) }} className={`mono rounded-md px-2 py-1 ${batch === b ? 'bg-white text-slate-900' : 'bg-white/10'}`}>{b}</button>)}</div>
              <div className="flex items-center gap-1 text-xs text-slate-400">Velocidad:
                {SPEEDS.map(s => <button key={s.v} onClick={() => setSpeed(s.v)} className={`mono rounded-md px-2 py-1 ${speed === s.v ? 'bg-white text-slate-900' : 'bg-white/10'}`}>{s.l}</button>)}</div>
              <button onClick={run} disabled={!q} className="rounded-xl bg-teal-300 px-5 py-2 font-semibold text-slate-900 hover:bg-teal-200 disabled:opacity-40">{running ? 'Ejecutando…' : t > 0 ? '↻ Repetir' : '▶ Ejecutar'}</button>
            </div>
          </SpotlightCard>

          <div className="grid gap-4 md:grid-cols-2">
            <SpotlightCard spotlightColor="rgba(94,234,212,.25)">
              <div className="mb-3 flex items-baseline justify-between"><h3 className="font-semibold text-teal-200">A · Fusión clásica</h3>
                <span className="mono text-2xl">{Math.min(t, endA).toFixed(0)}<small className="text-xs text-slate-400"> ms</small></span></div>
              <div className="space-y-2">
                <Stage name="BM25 (léxico)" sub="índice invertido, stemming" p={bmP} color="#5eead4" />
                <Stage name="BGE (embeddings)" sub="búsqueda vectorial · en paralelo" p={bgeP} color="#5eead4" ms={S} />
                <Stage name="Fusión convexa α=0.85" sub="min-max + combinación lineal" p={Math.max(0, Math.min(1, (t - S) / F))} color="#5eead4" ms={F} />
              </div>
              <div className="mt-4"><Top ids={q?.rankA ?? []} show={doneA} label="fusión" color="#5eead4" /></div>
            </SpotlightCard>

            <SpotlightCard spotlightColor="rgba(168,85,247,.28)">
              <div className="mb-3 flex items-baseline justify-between"><h3 className="font-semibold text-violet-300">B · sLLM local por lotes</h3>
                <span className="mono text-2xl">{Math.min(t, endB).toFixed(0)}<small className="text-xs text-slate-400"> ms</small></span></div>
              <div className="space-y-2">
                <Stage name="Recuperación híbrida" sub="BM25 ‖ BGE → candidatos" p={Math.min(1, t / S)} color="#a855f7" ms={S} />
                <Stage name={`Qwen2.5-3B · lotes de ${batch}`} sub={`${nb} pasadas × ${batch} docs · puntuación 0–4 (RG-S)`} p={Math.max(0, Math.min(1, (t - S) / L))} color="#a855f7" ms={L} />
              </div>
              <div className="mt-3 flex flex-wrap gap-1">{(q?.rankA ?? []).map((id, i) => { const ok = scored(i) && t > 0; const c = byId[id]; return (
                <span key={id} title={ok ? `score ${c.llm.toFixed(3)}` : 'pendiente'} className={`mono flex h-6 w-9 items-center justify-center rounded text-[10px] transition-all duration-300 ${ok ? (c.rel > 0 ? 'bg-emerald-400/30 text-emerald-200' : 'bg-violet-400/25 text-violet-200') : 'bg-white/5 text-slate-600'}`}>{ok ? c.llm.toFixed(2).slice(1) : '··'}</span>) })}</div>
              <div className="mt-4"><Top ids={q?.rankB ?? []} show={doneB} label="LLM" color="#a855f7" /></div>
            </SpotlightCard>
          </div>
          {doneA && q && <p className="text-center text-sm text-slate-400">
            {doneB ? <>A respondió en <b className="text-teal-200">{endA.toFixed(0)} ms</b>; B en <b className="text-violet-300">{endB.toFixed(0)} ms</b> ({(endB / endA).toFixed(1)}× más lento). </> : <>A ya respondió; B sigue puntuando candidatos…</>}
            Cuadros verdes = documentos relevantes según los juicios (qrels) de FiQA.</p>}
        </div>
      </div>
    </section>
  )
}
