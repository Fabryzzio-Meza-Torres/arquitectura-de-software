import { useEffect, useState } from 'react'
import Aurora from './components/rb/Aurora'
import BlurText from './components/rb/BlurText'
import ShinyText from './components/rb/ShinyText'
import Demo from './Demo'
import Benchmarks from './Benchmarks'
import type { IdxItem, Summary } from './types'

export default function App() {
  const [idx, setIdx] = useState<IdxItem[]>([])
  const [sum, setSum] = useState<Summary | null>(null)
  useEffect(() => {
    fetch('/data/index.json').then(r => r.json()).then(setIdx)
    fetch('/data/summary.json').then(r => r.json()).then(setSum)
  }, [])
  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[640px] opacity-80">
        <Aurora colorStops={['#5eead4', '#6366f1', '#a855f7']} amplitude={1.1} speed={0.6} />
      </div>
      <header className="relative mx-auto max-w-6xl px-6 pt-24 pb-16 text-center">
        <span className="mono rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-teal-200">
          Arquitectura de recuperación y ranking · FiQA · 648 consultas reales
        </span>
        <h1 className="mt-6 text-6xl font-semibold tracking-tight md:text-7xl">
          <BlurText text="MINION" animateBy="letters" delay={80} />
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-xl text-slate-300">
          <ShinyText text="Encuentra el documento correcto en segundos, no en horas." color="#cbd5e1" shineColor="#ffffff" speed={3} />
        </p>
        <p className="mx-auto mt-4 max-w-2xl text-slate-400">
          Recuperación híbrida (BM25 + embeddings) con dos formas de ordenar los resultados: la <b className="text-slate-200">fusión clásica</b> y
          un <b className="text-slate-200">LLM pequeño y local</b> que puntúa cada candidato por lotes. Corre en tu infraestructura: tus documentos no salen de casa.
        </p>
        <div className="mt-8 flex justify-center gap-3 text-sm">
          <a href="#demo" className="rounded-xl bg-white px-5 py-2.5 font-medium text-slate-900 hover:bg-slate-200">Ver el flujo en vivo</a>
          <a href="#bench" className="rounded-xl border border-white/20 px-5 py-2.5 hover:bg-white/10">Resultados medidos</a>
        </div>
      </header>
      <main className="relative mx-auto max-w-6xl space-y-24 px-6 pb-24">
        <Demo idx={idx} sum={sum} />
        {sum && <Benchmarks sum={sum} />}
        <footer className="border-t border-white/10 pt-6 text-xs text-slate-500">
          Datos: experimento MINION v2 (FiQA-2018, corpus de 10 000 docs, Qwen2.5-3B-Instruct + BGE-base). Los tiempos del flujo en vivo se reproducen a partir de las mediciones reales de cada consulta.
        </footer>
      </main>
    </div>
  )
}
