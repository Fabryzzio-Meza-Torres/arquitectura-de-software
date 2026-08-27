import { useMemo, useState } from 'react'
import { api } from '../api/client'
import { Empty, Money, Notice, Section, StatusBadge } from '../components'
import { usePolling, useRequestSequence } from '../hooks'

export default function LeasingView({ user }) {
  const [applications, setApplications] = useState([])
  const [queue, setQueue] = useState([])
  const [contracts, setContracts] = useState([])
  const [audit, setAudit] = useState([])
  const [summary, setSummary] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [notice, setNotice] = useState({})
  const [busy, setBusy] = useState(false)
  const selected = useMemo(() => applications.find((item) => item.id === Number(selectedId)), [applications, selectedId])
  const activeContracts = contracts.filter((item) => item.status === 'ACTIVE' || item.status === 'PENDING')
  const closedContracts = contracts.filter((item) => item.status === 'COMPLETED_PURCHASED' || item.status === 'COMPLETED_RETURNED')

  const { start, isCurrent } = useRequestSequence()

  async function load() {
    const seq = start()
    try {
      const [nextApplications, nextQueue, nextContracts, nextAudit, nextSummary] = await Promise.all([
        api('/api/requests'), api('/api/review-queue'), api('/api/contracts'), api('/api/audit'), api('/api/collections/summary'),
      ])
      if (!isCurrent(seq)) return
      setApplications(nextApplications); setQueue(nextQueue); setContracts(nextContracts); setAudit(nextAudit); setSummary(nextSummary)
      if (!selectedId && nextApplications[0]) setSelectedId(nextApplications[0].id)
      setNotice((current) => (current.error ? {} : current))
    } catch (error) { if (isCurrent(seq)) setNotice({ error: error.message }) }
  }
  usePolling(load)

  async function sendCollectionMessage(contractId) {
    setBusy(true); setNotice({})
    try {
      const result = await api(`/api/contracts/${contractId}/collection-message`, { method: 'POST', body: {} })
      setNotice({ success: `Mensaje formal enviado (nivel ${result.level}).` }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function processResolution(contractId) {
    setBusy(true); setNotice({})
    try {
      await api(`/api/contracts/${contractId}/resolution/process`, { method: 'POST' })
      setNotice({ success: 'Cierre de contrato procesado.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function simulateExternalOutcome(event) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const outcome = values.get('outcome')
    const body = {
      application_id: Number(selectedId), outcome,
      reason_code: outcome === 'APPROVED' ? 'EXTERNAL_POLICY_APPROVED' : `EXTERNAL_${outcome}`,
      reason_text: outcome === 'APPROVED' ? 'External evaluator confirmed policy compliance.' : 'External evaluator supplied a documented outcome with sufficient justification.',
      approved_limit: outcome === 'APPROVED' ? Number(selected.requested_amount) : null,
      approved_term_months: outcome === 'APPROVED' ? Number(selected.requested_term_months) : null,
      annual_interest_rate: outcome === 'APPROVED' ? Number(values.get('annual_rate')) : null,
    }
    setBusy(true); setNotice({})
    try {
      await api('/api/integrations/risk-outcomes', { method: 'POST', body, headers: { 'X-Integration-Key': 'poc-risk-secret' } })
      setNotice({ success: 'Callback externo registrado. Lea$e no calculó el resultado.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function attest() {
    setBusy(true); setNotice({})
    try {
      await api(`/api/requests/${selectedId}/decision-attestations`, { method: 'POST', body: {} })
      setNotice({ success: `Atestación registrada por ${user.name}.` }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function activate(event) {
    event.preventDefault()
    const rate = Number(new FormData(event.currentTarget).get('exchange_rate'))
    setBusy(true); setNotice({})
    try {
      await api(`/api/requests/${selectedId}/activate`, { method: 'POST', body: { exchange_rate: rate } })
      setNotice({ success: 'Contrato y cronograma activados exactamente una vez.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  return (
    <main className="dashboard" aria-busy={busy}>
      <div className="hero-card leasing-hero"><div><p className="eyebrow">Head of Credit & Collections · Leasing company</p><h1>Control sin cajas negras.</h1><p>Registra resultados externos, activa contratos y conserva cada transición.</p><p className="microcopy">Juan Pedro: registra el resultado externo, activa el contrato y procesa el cierre. César sube documentos y paga; Maxim negocia.</p></div><div className="metric-cluster"><div><span>{queue.length}</span><small>en cola</small></div><div><span>{contracts.length}</span><small>activos</small></div></div></div>
      <Notice {...notice} />
      <div className="two-column">
        <Section eyebrow="Pipeline" title="Solicitudes visibles">
          {applications.length === 0 ? <Empty>Sin solicitudes.</Empty> : <div className="stack-list">{applications.map((item) => <button key={item.id} onClick={() => setSelectedId(item.id)} className={`list-row ${Number(selectedId) === item.id ? 'active' : ''}`}><span><strong>#{item.id} · {item.machinery_type}</strong><small>{item.ruc} · <Money amount={item.requested_amount} currency={item.currency} /></small></span><StatusBadge value={item.status} /></button>)}</div>}
        </Section>
        <Section eyebrow="Review queue" title="SLA y buró"><div className="kpi-grid"><div><small>Pendientes</small><strong>{queue.length}</strong></div><div><small>Scoring unavailable</small><strong>{queue.filter((item) => item.status === 'SCORING_UNAVAILABLE').length}</strong></div><div><small>Con score</small><strong>{queue.filter((item) => item.bureau_score).length}</strong></div></div></Section>
      </div>

      {selected && <div className="two-column">
        <Section eyebrow={`Solicitud #${selected.id}`} title="Resultado del evaluador externo">
          <p className="scope-note">Este panel simula un callback externo para la POC. Juan Pedro no evalúa riesgo ni decide crédito.</p>
          <div className="summary-strip compact"><div><small>Estado</small><StatusBadge value={selected.status} /></div><div><small>Score recibido</small><strong>{selected.bureau_score ?? 'No disponible'}</strong></div></div>
          {['IN_REVIEW', 'SCORING_UNAVAILABLE'].includes(selected.status) && <form className="form-grid" onSubmit={simulateExternalOutcome}><label>Outcome externo<select name="outcome"><option>APPROVED</option><option>CONDITIONED</option><option>REJECTED</option></select></label><label>Tasa anual %<input name="annual_rate" type="number" step="0.01" min="0" defaultValue="12" /></label><button className="primary span-2" disabled={busy}>Simular callback externo</button></form>}
          {selected.pending_outcome && ['IN_REVIEW', 'SCORING_UNAVAILABLE'].includes(selected.status) && <>
            <p className="microcopy">Monto sobre PEN 500 000: requiere atestación de dos cuentas de leasing distintas (NFR-07) antes de aplicarse.</p>
            <button onClick={attest}>Atestar resultado recibido</button>
          </>}
          {selected.decision_reason_text && <div className="decision-box"><StatusBadge value={selected.status} /><strong>{selected.decision_reason_code}</strong><p>{selected.decision_reason_text}</p></div>}
        </Section>

        <Section eyebrow="Activación" title="Fijar contrato">
          <p>Activación exige resultado externo APPROVED y un cronograma firmado; el contrato queda PENDING hasta que el cliente confirme la recepción.</p>
          <form className="inline-form" onSubmit={activate}><label>Tipo de cambio<input name="exchange_rate" type="number" min="0.000001" step="0.000001" defaultValue={selected.currency === 'PEN' ? '1' : '3.75'} readOnly={selected.currency === 'PEN'} /></label><button className="primary" disabled={busy || selected.status !== 'APPROVED'}>Activar una vez</button></form>
          {selected.currency === 'PEN' && <p className="microcopy">Soles: tipo de cambio fijo en 1 (no aplica conversión).</p>}
          {contracts.filter((item) => item.application_id === selected.id).map((contract) => <div className="contract-summary" key={contract.id}><div><StatusBadge value={contract.status} /><strong>Contrato #{contract.id}</strong></div><span><Money amount={contract.outstanding_balance} currency={contract.currency} /> · TC {contract.locked_exchange_rate}</span></div>)}
        </Section>
      </div>}

      <div className="two-column">
        <Section eyebrow="VG3" title="Cobranzas: ingreso pronosticado y mora">
          {!summary ? <Empty>Sin datos de cobranzas aún.</Empty> : <>
            <div className="kpi-grid">
              {Object.entries(summary.pronosticated_income_by_currency).map(([currency, amount]) => (
                <div key={currency}><small>Ingreso pronosticado {currency}</small><strong><Money amount={amount} currency={currency} /></strong></div>
              ))}
              {Object.entries(summary.receivable_by_currency).map(([currency, amount]) => (
                <div key={`receivable-${currency}`}><small>Por cobrar {currency}</small><strong><Money amount={amount} currency={currency} /></strong></div>
              ))}
            </div>
            <div className="record-grid">{summary.delinquency_buckets.map((bucket) => (
              <div key={bucket.level}><h3><StatusBadge value={bucket.level} /></h3><p>{bucket.count} contrato(s) · <Money amount={bucket.outstanding_total} currency="PEN" /></p></div>
            ))}</div>
          </>}
        </Section>

        <Section eyebrow="Cartera activa" title="Contratos y mora">
          {activeContracts.length === 0 ? <Empty>Sin contratos activos.</Empty> : <div className="stack-list">{activeContracts.map((contract) => (
            <div className="list-row" key={contract.id}>
              <span><strong>Contrato #{contract.id}</strong><small><Money amount={contract.outstanding_balance} currency={contract.currency} /></small></span>
              <div className="inline-status">
                {contract.delinquency_level && <StatusBadge value={contract.delinquency_level} />}
                {contract.delinquency_level && contract.delinquency_level !== 'GREEN' && <button onClick={() => sendCollectionMessage(contract.id)} disabled={busy}>Enviar mensaje formal</button>}
                {contract.resolution_choice && contract.status === 'ACTIVE' && <button className="primary" onClick={() => processResolution(contract.id)} disabled={busy}>Procesar {contract.resolution_choice}</button>}
              </div>
            </div>
          ))}</div>}
        </Section>
      </div>

      <Section eyebrow="VG4" title="Acuerdos cerrados">
        {closedContracts.length === 0 ? <Empty>Ningún contrato cerrado todavía.</Empty> : <div className="stack-list">{closedContracts.map((contract) => (
          <div className="list-row" key={contract.id}><span><strong>Contrato #{contract.id}</strong><small>Resuelto {contract.resolved_at ? new Date(contract.resolved_at).toLocaleString('es-PE') : ''}</small></span><StatusBadge value={contract.status} /></div>
        ))}</div>}
      </Section>

      <Section eyebrow="KPD-6" title="Auditoría append-only">
        {audit.length === 0 ? <Empty>Sin transiciones aún.</Empty> : <div className="audit-list">{audit.slice(0, 12).map((entry) => <div key={entry.id}><span className="audit-dot" /><p><strong>{entry.action}</strong><small>{entry.entity_type} #{entry.entity_id} · {new Date(entry.created_at).toLocaleString('es-PE')}</small></p><code>{entry.previous_value || '∅'} → {entry.new_value || '∅'}</code></div>)}</div>}
      </Section>
    </main>
  )
}

