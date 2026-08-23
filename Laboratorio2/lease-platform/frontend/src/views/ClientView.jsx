import { useEffect, useMemo, useState } from 'react'
import { api, downloadFile } from '../api/client'
import { Empty, Money, Notice, Section, StatusBadge } from '../components'
import { readDraft, saveDraft, usePolling, useRequestSequence } from '../hooks'

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

export default function ClientView({ user }) {
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

  const [payments, setPayments] = useState([])
  const { start, isCurrent } = useRequestSequence()

  async function load() {
    const seq = start()
    try {
      const [nextApplications, nextContracts] = await Promise.all([api('/api/requests'), api('/api/contracts')])
      if (!isCurrent(seq)) return
      setApplications(nextApplications)
      setContracts(nextContracts)
      const activeId = selectedId || nextApplications[0]?.id
      if (activeId) {
        setSelectedId(activeId)
        const [nextDocuments, nextSimulations] = await Promise.all([
          api(`/api/requests/${activeId}/documents`),
          api(`/api/requests/${activeId}/simulations`),
        ])
        let nextNegotiation = null
        try { nextNegotiation = await api(`/api/requests/${activeId}/negotiation`) } catch { nextNegotiation = null }
        const activeContract = nextContracts.find((item) => item.application_id === Number(activeId))
        const nextPayments = activeContract ? await api(`/api/contracts/${activeContract.id}/payments`) : []
        if (!isCurrent(seq)) return
        setDocuments(nextDocuments)
        setSimulations(nextSimulations)
        setNegotiation(nextNegotiation)
        setPayments(nextPayments)
      }
      setNotice((current) => (current.error ? {} : current))
    } catch (error) {
      if (isCurrent(seq)) setNotice({ error: error.message })
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
      await api(`/api/simulations/${id}/accept`, { method: 'POST', body: { signer_confirmation: user.name } })
      setNotice({ success: 'Cronograma firmado; hash de integridad registrado.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function respondMeeting(meetingId, action) {
    setBusy(true); setNotice({})
    try {
      await api(`/api/negotiations/${negotiation.id}/meetings/${meetingId}/response`, { method: 'POST', body: { action, note: `Respuesta explícita de ${user.name}: ${action}` } })
      setNotice({ success: 'Respuesta registrada; Lea$e no tomó ninguna decisión por ti.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function updateReception(status) {
    setBusy(true); setNotice({})
    try {
      const note = status === 'CONFIRMED' ? 'Recepción confirmada por el cliente' : 'Recepción rechazada por el cliente'
      await api(`/api/contracts/${contract.id}/reception-status`, { method: 'POST', body: { status, note } })
      setNotice({ success: status === 'CONFIRMED' ? 'Recepción confirmada; cronograma generado.' : 'Rechazo registrado; Juan Pedro fue notificado.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function registerPayment(event) {
    event.preventDefault()
    const form = event.currentTarget
    const values = new FormData(form)
    setBusy(true); setNotice({})
    try {
      await api(`/api/contracts/${contract.id}/payments`, { method: 'POST', body: { bank_reference: values.get('bank_reference'), amount: Number(values.get('amount')) } })
      form.reset()
      setNotice({ success: 'Pago registrado y conciliado contra el cronograma.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  async function chooseResolution(choice) {
    setBusy(true); setNotice({})
    try {
      await api(`/api/contracts/${contract.id}/resolution`, { method: 'POST', body: { choice } })
      setNotice({ success: choice === 'PURCHASE' ? 'Opción de compra elegida.' : 'Devolución elegida.' }); await load()
    } catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  return (
    <main className="dashboard" aria-busy={busy}>
      <div className="hero-card client-hero">
        <div><p className="eyebrow">Head of Finance · Client company</p><h1>Capital listo para el proyecto.</h1><p>Solicita, observa y firma. Sin perseguir correos ni adivinar tasas.</p><p className="microcopy">César: crea la solicitud, sube documentos, firma el cronograma, confirma recepción y paga. Los resultados de crédito los registra Juan Pedro; la negociación la lleva Maxim.</p></div>
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
          {selected.status !== 'SUBMITTED' && documents.length > 0 && <div className="record-grid">
            <div><h3>Documentos del expediente</h3>{documents.map((doc) => <p key={doc.id}><strong>{doc.kind.replaceAll('_', ' ')}</strong><br />{doc.quarantined ? 'Rechazado por antivirus' : doc.original_name}</p>)}</div>
          </div>}
        </Section>

        <div className="two-column">
          <Section eyebrow="Flow 1B" title="Negociación registrada">
            {!negotiation ? <Empty>Broker aún no abrió negociación.</Empty> : <>
              <div className="inline-status"><StatusBadge value={negotiation.state} /><span>{negotiation.documents.length} documento(s)</span></div>
              {negotiation.meetings.map((meeting) => <div className="timeline-row" key={meeting.id}><div><strong>{new Date(meeting.scheduled_for).toLocaleString('es-PE')}</strong><small>Propuesta #{meeting.id} · {meeting.state}</small></div>{meeting.state === 'PROPOSED' && <div className="button-row"><button onClick={() => respondMeeting(meeting.id, 'ACCEPTED')}>Aceptar</button><button className="ghost" onClick={() => respondMeeting(meeting.id, 'REJECTED')}>Rechazar</button></div>}</div>)}
              {negotiation.documents.map((doc) => <div className="document-line" key={doc.id}><strong>{doc.original_name}</strong><span>{doc.summary}</span><button className="ghost" onClick={() => downloadFile(`/api/negotiations/${negotiation.id}/documents/${doc.id}/download`, doc.original_name)}>Descargar PDF</button></div>)}
              {negotiation.messages.length > 0 && <div className="record-grid"><div><h3>Mensajes de Maxim</h3>{negotiation.messages.map((message) => <p key={message.id}><strong>{message.recipients}</strong>: {message.body} <StatusBadge value={message.delivery_status} /></p>)}</div></div>}
            </>}
          </Section>

          <Section eyebrow="Flow 3" title="Cronograma de pagos (simulaciones)">
            {selected.status !== 'APPROVED' ? <Empty>Disponible cuando Juan Pedro registre el resultado externo APPROVED.</Empty> : <>
              <p className="microcopy">Genera hasta 3 opciones de cronograma y firma una para poder activar el contrato.</p>
              <form className="inline-form" onSubmit={createSimulation}><label>Gracia<input name="grace_months" type="number" min="0" max="6" defaultValue="0" /></label><label>Balloon %<input name="balloon_percent" type="number" min="0" max="40" defaultValue="0" /></label><button className="primary" disabled={simulations.length >= 3}>Simular</button></form>
              {simulations.map((simulation) => <div className="simulation-card" key={simulation.id}><div><strong>Opción #{simulation.id}</strong><small>{simulation.installments.length} cuotas · interés {simulation.annual_interest_rate}%</small></div><div><strong><Money amount={simulation.total_cost} currency={selected.currency} /></strong><small>Costo total</small></div>{simulation.accepted ? <StatusBadge value="SIGNED" /> : <button onClick={() => acceptSimulation(simulation.id)}>Elegir y firmar</button>}</div>)}
            </>}
          </Section>
        </div>

        <Section eyebrow="Contrato" title={contract ? `Contrato #${contract.id} · ${contract.status}` : 'Esperando activación'}>
          {!contract ? <Empty>Juan Pedro activará el contrato cuando exista cronograma firmado.</Empty> : <>
            <div className="contract-metrics"><div><small>Saldo</small><strong><Money amount={contract.outstanding_balance} currency={contract.currency} /></strong></div><div><small>Tipo de cambio fijado</small><strong>{contract.locked_exchange_rate}</strong></div><div><small>Recepción</small><StatusBadge value={contract.reception_status} /></div>{contract.delinquency_level && <div><small>Nivel de mora</small><StatusBadge value={contract.delinquency_level} /></div>}</div>

            {contract.status === 'PENDING' && <>
              <p className="microcopy">Confirma la recepción de la maquinaria para generar el cronograma ejecutable y activar el contrato.</p>
              <div className="button-row"><button onClick={() => updateReception('CONFIRMED')}>Confirmar recepción</button><button className="ghost" onClick={() => updateReception('REJECTED')}>Reportar rechazo</button></div>
            </>}

            {contract.installments.length > 0 && <>
              <div className="schedule-table" role="region" aria-label="Cronograma de cuotas" tabIndex="0"><table><thead><tr><th>Cuota</th><th>Vencimiento</th><th>Monto</th><th>Pagado</th></tr></thead><tbody>{contract.installments.map((item) => <tr key={item.id}><td>{item.number}</td><td>{item.due_date}</td><td><Money amount={item.amount} currency={contract.currency} /></td><td><Money amount={item.paid_amount} currency={contract.currency} /></td></tr>)}</tbody></table></div>

              {contract.status === 'ACTIVE' && <>
                <form className="inline-form" onSubmit={registerPayment}>
                  <label>Referencia bancaria<input required name="bank_reference" placeholder="BCP-2027-000123" /></label>
                  <label>Monto<input required name="amount" type="number" min="0.01" step="0.01" /></label>
                  <button className="primary" disabled={busy}>Registrar pago</button>
                </form>
                <p className="microcopy">Reenviar la misma referencia bancaria no duplica el pago (idempotente).</p>

                <h3>Fin de contrato</h3>
                {contract.resolution_choice ? <Notice success={`Elegiste ${contract.resolution_choice}. Esperando que Juan Pedro procese el cierre.`} /> : <div className="button-row">
                  <button className="primary" disabled={busy || Number(contract.outstanding_balance) !== 0} onClick={() => chooseResolution('PURCHASE')}>Ejercer opción de compra</button>
                  <button className="ghost" disabled={busy} onClick={() => chooseResolution('RETURN')}>Devolver equipo</button>
                </div>}
                {Number(contract.outstanding_balance) !== 0 && <p className="microcopy">La opción de compra requiere saldo cero; hoy debes <Money amount={contract.outstanding_balance} currency={contract.currency} />.</p>}
              </>}

              {(contract.status === 'COMPLETED_PURCHASED' || contract.status === 'COMPLETED_RETURNED') && <Notice success={`Contrato cerrado: ${contract.status}.`} />}
            </>}

            {payments.length > 0 && <div className="record-grid"><div><h3>Pagos registrados</h3>{payments.map((payment) => <p key={payment.id}><strong>{payment.bank_reference}</strong>: <Money amount={payment.amount} currency={payment.currency} /> <StatusBadge value={payment.reconciliation_status} /></p>)}</div></div>}
          </>}
        </Section>
      </>}
    </main>
  )
}
