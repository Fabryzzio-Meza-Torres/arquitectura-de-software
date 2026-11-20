import SpotlightCard from './components/rb/SpotlightCard'
import CountUp from './components/rb/CountUp'
import type { Summary } from './types'

const NAMES: Record<string, string> = { 'p@3': 'P@3', 'ndcg@3': 'nDCG@3', 'mrr@10': 'MRR@10', 'p@5': 'P@5', 'ndcg@5': 'nDCG@5' }

export default function Benchmarks({ sum }: { sum: Summary }) {
  const m = sum.quality.metrics, lat = sum.latency
  const max = Math.max(...Object.values(m).map(x => Math.max(x.A, x.B)))
  const ratio = lat.B.p50_ms / lat.A.p50_ms
  return (
    <section id="bench" className="scroll-mt-8">
      <h2 className="text-3xl font-semibold">Resultados medidos</h2>
      <p className="mt-2 max-w-3xl text-slate-400">FiQA-2018 · {sum.quality.queries} consultas · 10 000 documentos · hasta 20 candidatos por consulta · IC 95 % por bootstrap.</p>

      <div className="mt-6 grid gap-4 md:grid-cols-4">
        {[{ l: 'Latencia p50 · A', v: lat.A.p50_ms, c: 'text-teal-200' }, { l: 'Latencia p50 · B', v: lat.B.p50_ms, c: 'text-violet-300' },
          { l: 'p99 · A', v: lat.A.p99_ms, c: 'text-teal-200' }, { l: 'p99 · B', v: lat.B.p99_ms, c: 'text-violet-300' }].map(k => (
          <SpotlightCard key={k.l}><div className="text-xs text-slate-400">{k.l}</div>
            <div className={`mono text-4xl font-semibold ${k.c}`}><CountUp to={k.v} decimals={0} duration={1.4} /><small className="text-base text-slate-400"> ms</small></div></SpotlightCard>))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <SpotlightCard>
          <h3 className="mb-4 font-semibold">Calidad del ranking</h3>
          <div className="space-y-4">{Object.entries(m).map(([k, v]) => (
            <div key={k}><div className="mb-1 flex justify-between text-xs"><span className="font-medium">{NAMES[k] ?? k}</span>
              <span className={`mono ${v.delta < 0 ? 'text-amber-300' : 'text-emerald-300'}`}>Δ B−A = {v.delta.toFixed(3)}  [{v.CI95[0].toFixed(3)}, {v.CI95[1].toFixed(3)}]</span></div>
              {(['A', 'B'] as const).map(a => <div key={a} className="mb-1 flex items-center gap-2"><span className="w-3 text-xs text-slate-400">{a}</span>
                <div className="h-3 flex-1 rounded bg-white/5"><div className="h-full rounded" style={{ width: `${(v[a] / max) * 100}%`, background: a === 'A' ? '#5eead4' : '#a855f7' }} /></div>
                <span className="mono w-14 text-right text-xs">{v[a].toFixed(3)}</span></div>)}</div>))}</div>
        </SpotlightCard>

        <div className="space-y-4">
          <SpotlightCard>
            <h3 className="mb-3 font-semibold">Tamaño de lote del LLM (mismo cómputo)</h3>
            <table className="mono w-full text-sm"><thead className="text-left text-xs text-slate-400"><tr><th>Lote</th><th>Tiempo medio</th><th>vs lote 1</th></tr></thead><tbody>
              {Object.entries(sum.batching).map(([b, v]) => <tr key={b} className="border-t border-white/5"><td className="py-1.5">{b}</td><td>{v.mean_s.toFixed(2)} s</td><td>{(v.mean_s / sum.batching['1'].mean_s).toFixed(2)}×</td></tr>)}</tbody></table>
          </SpotlightCard>
          <SpotlightCard>
            <h3 className="mb-3 font-semibold">Concurrencia (arquitectura B)</h3>
            <table className="mono w-full text-sm"><thead className="text-left text-xs text-slate-400"><tr><th>Clientes</th><th>Throughput</th><th>p99</th><th>≤ 2.5 s</th></tr></thead><tbody>
              {sum.concurrency.map(c => <tr key={c.concurrency} className="border-t border-white/5"><td className="py-1.5">{c.concurrency}</td><td>{c.throughput_requests_per_s.toFixed(2)} req/s</td><td>{c.p99_ms.toFixed(0)} ms</td><td>{(c.continuity_within_2500_ms * 100).toFixed(0)} %</td></tr>)}</tbody></table>
          </SpotlightCard>
        </div>
      </div>

      <SpotlightCard className="mt-4" spotlightColor="rgba(251,191,36,.2)">
        <h3 className="font-semibold text-amber-200">Lectura honesta de los datos</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
          <li>En calidad, la fusión clásica (A) supera al sLLM (B) en todas las métricas, con IC 95 % que no cruza el cero (p. ej. nDCG@3 {m['ndcg@3'].A.toFixed(3)} vs {m['ndcg@3'].B.toFixed(3)}).</li>
          <li>B es ~{ratio.toFixed(0)}× más lento en p50 y bajo carga concurrente la GPU serializa las solicitudes: el p99 sube con los clientes.</li>
          <li>Procesar en lotes de 4 u 8 no aceleró frente al lote 1 en este hardware; además cambia ligeramente los scores por el relleno (padding).</li>
          <li>Qué sí aporta B: scoring continuo 0–1 explicable por documento, ejecución 100 % local y sin ajuste de α. Es el punto de partida para un reranker afinado.</li>
        </ul>
      </SpotlightCard>
    </section>
  )
}
