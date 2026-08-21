import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import { Empty, Money, Notice, Section, StatusBadge } from '../components'
import { readDraft, saveDraft, usePolling } from '../hooks'

const tomorrowYear = () => {
  const value = new Date()
  value.setFullYear(value.getFullYear() + 1)
  return value.toISOString().slice(0, 10)
}

const initialForm = {
  ruc: '20123456789',
  machinery_type: 'Excavadora hidráulica',
  requested_term_months: 12,
  requested_amount: 250000,
  currency: 'PEN',
  expected_settlement_date: tomorrowYear(),
}

export default function ClientView() {
  const [form, setForm] = useState(() => readDraft('lease-request-draft', initialForm))
  const [applications, setApplications] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [documents, setDocuments] = useState([])
  const [simulations, setSimulations] = useState([])
  const [contracts, setContracts] = useState([])
  const [negotiation, setNegotiation] = useState(null)
  const [notice, setNotice] = useState({})
  const [busy, setBusy] = useState(false)

  const selected = useMemo(() => applications.find((item) => item.id === Number(selectedId)), [applications, selectedId])
  const contract = contracts.find((item) => item.application_id === Number(selectedId))

  async function load() {
    try {
      const [nextApplications, nextContracts] = await Promise.all([api('/api/requests'), api('/api/contracts')])
      setApplications(nextApplications)
      setContracts(nextContracts)
      const activeId = selectedId || nextApplications[0]?.id
      if (activeId) {
        setSelectedId(activeId)
        const [nextDocuments, nextSimulations] = await Promise.all([
          api(`/api/requests/${activeId}/documents`),
          api(`/api/requests/${activeId}/simulations`),
        ])
        setDocuments(nextDocuments)
        setSimulations(nextSimulations)
        try { setNegotiation(await api(`/api/requests/${activeId}/negotiation`)) } catch { setNegotiation(null) }
      }
    } catch (error) {
      setNotice({ error: error.message })
    }
  }

  usePolling(load)
  useEffect(() => saveDraft('lease-request-draft', form), [form])
  useEffect(() => { if (selectedId) load() }, [selectedId]) // eslint-disable-line react-hooks/exhaustive-deps

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function createRequest(event) {
    event.preventDefault()
    setBusy(true); setNotice({})
    try {
      const created = await api('/api/requests', { method: 'POST', body: { ...form, requested_term_months: Number(form.requested_term_months), requested_amount: Number(form.requested_amount) }, retryNetwork: true })
      setSelectedId(created.id)
      localStorage.removeItem('lease-request-draft')
      setNotice({ success: `Solicitud #${created.id} creada sin duplicados.` })
      await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function uploadDocument(event, kind) {
    const file = event.target.files?.[0]
    if (!file || !selectedId) return
    const data = new FormData()
    data.append('kind', kind)
    data.append('file', file)
    setBusy(true); setNotice({})
    try {
      await api(`/api/requests/${selectedId}/documents`, { method: 'POST', body: data })
      setNotice({ success: `${kind} procesado.` }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false); event.target.value = '' }
  }

  async function submitForReview() {
    setBusy(true); setNotice({})
    try {
      await api(`/api/requests/${selectedId}/submit`, { method: 'POST', body: { bureau_scenario: 'SUCCESS', bureau_score: 720 } })
      setNotice({ success: 'Expediente enviado. El resultado será recibido desde el evaluador externo.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function createSimulation(event) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    setBusy(true); setNotice({})
    try {
      await api(`/api/requests/${selectedId}/simulations`, { method: 'POST', body: { grace_months: Number(values.get('grace_months')), frequency: 'MONTHLY', balloon_percent: Number(values.get('balloon_percent')) } })
      setNotice({ success: 'Simulación generada con precisión decimal.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function acceptSimulation(id) {
    setBusy(true); setNotice({})
    try {
      await api(`/api/simulations/${id}/accept`, { method: 'POST', body: { signer_confirmation: 'César — Head of Finance' } })
      setNotice({ success: 'Cronograma firmado; hash de integridad registrado.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function respondMeeting(meetingId, action) {
    setBusy(true); setNotice({})
    try {
      await api(`/api/negotiations/${negotiation.id}/meetings/${meetingId}/response`, { method: 'POST', body: { action, note: `Respuesta explícita de César: ${action}` } })
      setNotice({ success: 'Respuesta registrada; Lea$e no tomó ninguna decisión por ti.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function updateReception(status) {
    setBusy(true); setNotice({})
    try {
      await api(`/api/contracts/${contract.id}/reception-status`, { method: 'POST', body: { status, note: 'Estado informado por el cliente' } })
      setNotice({ success: `Recepción marcada ${status}. No se coordinó logística.` }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  return (
    <main className="dashboard" aria-busy={busy}>
      <div className="hero-card client-hero">
        <div><p className="eyebrow">Head of Finance · Client company</p><h1>Capital listo para el proyecto.</h1><p>Solicita, observa y firma. Sin perseguir correos ni adivinar tasas.</p></div>
        <div className="hero-metric"><span>{applications.length}</span><small>solicitudes visibles</small></div>
      </div>
      <Notice {...notice} />

      <div className="two-column">
        <Section eyebrow="Flow 1" title="Nueva solicitud">
          <form className="form-grid" onSubmit={createRequest}>
            <label>RUC<input required name="ruc" inputMode="numeric" value={form.ruc} onChange={updateField} /></label>
            <label>Maquinaria<input required name="machinery_type" value={form.machinery_type} onChange={updateField} /></label>
            <label>Monto<input required name="requested_amount" type="number" min="1" step="0.01" value={form.requested_amount} onChange={updateField} /></label>
            <label>Plazo (meses)<input required name="requested_term_months" type="number" min="1" max="120" value={form.requested_term_months} onChange={updateField} /></label>
            <label>Moneda<select name="currency" value={form.currency} onChange={updateField}><option>PEN</option><option>USD</option></select></label>
            <label>Liquidación del proyecto<input required name="expected_settlement_date" type="date" value={form.expected_settlement_date} onChange={updateField} /></label>
            <button className="primary span-2" disabled={busy}>Crear solicitud</button>
          </form>
          <p className="microcopy">Borrador preservado localmente por 24 horas. Un reenvío idéntico devuelve la misma solicitud.</p>
        </Section>

        <Section eyebrow="Mis operaciones" title="Solicitudes">
          {applications.length === 0 ? <Empty>Aún no existe una solicitud.</Empty> : (
            <div className="stack-list">{applications.map((item) => (
              <button key={item.id} className={`list-row ${Number(selectedId) === item.id ? 'active' : ''}`} onClick={() => setSelectedId(item.id)}>
                <span><strong>#{item.id} · {item.machinery_type}</strong><small><Money amount={item.requested_amount} currency={item.currency} /> · {item.requested_term_months} meses</small></span>
                <StatusBadge value={item.status} />
              </button>
            ))}</div>
          )}
        </Section>
      </div>

      {selected && <>
        <Section eyebrow={`Solicitud #${selected.id}`} title="Expediente y resultado">
          <div className="summary-strip">
            <div><small>Estado</small><StatusBadge value={selected.status} /></div>
            <div><small>Resultado externo</small><strong>{selected.decision_reason_code || 'Pendiente'}</strong></div>
            <div><small>Justificación</small><strong>{selected.decision_reason_text || 'Aún no recibida'}</strong></div>
          </div>
          {selected.status === 'SUBMITTED' && <div className="document-grid">
            {['BANK_STATEMENTS', 'TAX_RETURN', 'PROJECT_CONTRACT'].map((kind) => (
              <label className="upload-card" key={kind}><span>{kind.replaceAll('_', ' ')}</span><small>{documents.some((doc) => doc.kind === kind && !doc.quarantined) ? '✓ Listo' : 'PDF/JPG/PNG · máx. 20 MB'}</small><input aria-label={`Subir ${kind}`} type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(event) => uploadDocument(event, kind)} /></label>
            ))}
            <button className="primary" onClick={submitForReview} disabled={busy || documents.filter((doc) => !doc.quarantined).length < 3}>Enviar a revisión externa</button>
          </div>}
        </Section>

        <div className="two-column">
          <Section eyebrow="Flow 1B" title="Negociación registrada">
            {!negotiation ? <Empty>Broker aún no abrió negociación.</Empty> : <>
              <div className="inline-status"><StatusBadge value={negotiation.state} /><span>{negotiation.documents.length} documento(s)</span></div>
              {negotiation.meetings.map((meeting) => <div className="timeline-row" key={meeting.id}><div><strong>{new Date(meeting.scheduled_for).toLocaleString('es-PE')}</strong><small>Propuesta #{meeting.id} · {meeting.state}</small></div>{meeting.state === 'PROPOSED' && <div className="button-row"><button onClick={() => respondMeeting(meeting.id, 'ACCEPTED')}>Aceptar</button><button className="ghost" onClick={() => respondMeeting(meeting.id, 'REJECTED')}>Rechazar</button></div>}</div>)}
              {negotiation.documents.map((doc) => <div className="document-line" key={doc.id}><strong>{doc.original_name}</strong><span>{doc.summary}</span></div>)}
            </>}
          </Section>

          <Section eyebrow="Flow 3" title="Simulaciones">
            {selected.status !== 'APPROVED' ? <Empty>Disponibles después de resultado APPROVED.</Empty> : <>
              <form className="inline-form" onSubmit={createSimulation}><label>Gracia<input name="grace_months" type="number" min="0" max="6" defaultValue="0" /></label><label>Balloon %<input name="balloon_percent" type="number" min="0" max="40" defaultValue="0" /></label><button className="primary" disabled={simulations.length >= 3}>Simular</button></form>
              {simulations.map((simulation) => <div className="simulation-card" key={simulation.id}><div><strong>Opción #{simulation.id}</strong><small>{simulation.installments.length} cuotas · interés {simulation.annual_interest_rate}%</small></div><div><strong><Money amount={simulation.total_cost} currency={selected.currency} /></strong><small>Costo total</small></div>{simulation.accepted ? <StatusBadge value="SIGNED" /> : <button onClick={() => acceptSimulation(simulation.id)}>Elegir y firmar</button>}</div>)}
            </>}
          </Section>
        </div>

        <Section eyebrow="Contrato" title={contract ? `Contrato activo #${contract.id}` : 'Esperando activación'}>
          {!contract ? <Empty>Juan Pedro activará el contrato cuando exista cronograma firmado.</Empty> : <>
            <div className="contract-metrics"><div><small>Saldo</small><strong><Money amount={contract.outstanding_balance} currency={contract.currency} /></strong></div><div><small>Tipo de cambio fijado</small><strong>{contract.locked_exchange_rate}</strong></div><div><small>Recepción</small><StatusBadge value={contract.reception_status} /></div></div>
            <div className="schedule-table" role="region" aria-label="Cronograma de cuotas" tabIndex="0"><table><thead><tr><th>Cuota</th><th>Vencimiento</th><th>Monto</th><th>Brecha</th></tr></thead><tbody>{contract.schedule.installments.map((item) => <tr key={item.id}><td>{item.number}</td><td>{item.due_date}</td><td><Money amount={item.amount} currency={contract.currency} /></td><td>{item.cash_flow_gap_days} días</td></tr>)}</tbody></table></div>
            <div className="button-row"><button onClick={() => updateReception('CONFIRMED')}>Confirmar recepción</button><button className="ghost" onClick={() => updateReception('REJECTED')}>Reportar rechazo</button></div>
          </>}
        </Section>
      </>}
    </main>
  )
}
