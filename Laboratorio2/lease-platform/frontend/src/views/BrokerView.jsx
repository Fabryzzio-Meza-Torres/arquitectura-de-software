import { useMemo, useState } from 'react'
import { api, downloadFile } from '../api/client'
import { Empty, Notice, Section, StatusBadge } from '../components'
import { usePolling, useRequestSequence } from '../hooks'

export default function BrokerView() {
  const [applications, setApplications] = useState([])
  const [negotiations, setNegotiations] = useState([])
  const [selectedApplicationId, setSelectedApplicationId] = useState(null)
  const [selectedNegotiationId, setSelectedNegotiationId] = useState(null)
  const [notice, setNotice] = useState({})
  const [busy, setBusy] = useState(false)
  const negotiation = useMemo(() => negotiations.find((item) => item.id === Number(selectedNegotiationId)), [negotiations, selectedNegotiationId])

  const { start, isCurrent } = useRequestSequence()

  async function load() {
    const seq = start()
    try {
      const [nextApplications, nextNegotiations] = await Promise.all([api('/api/broker/assignments'), api('/api/negotiations')])
      if (!isCurrent(seq)) return
      setApplications(nextApplications); setNegotiations(nextNegotiations)
      if (!selectedApplicationId && nextApplications[0]) setSelectedApplicationId(nextApplications[0].application_id)
      if (!selectedNegotiationId && nextNegotiations[0]) setSelectedNegotiationId(nextNegotiations[0].id)
      setNotice((current) => (current.error ? {} : current))
    } catch (error) { if (isCurrent(seq)) setNotice({ error: error.message }) }
  }
  usePolling(load)

  async function act(action, success) {
    setBusy(true); setNotice({})
    try { await action(); setNotice({ success }); await load() }
    catch (error) { setNotice({ error: error.message }) }
    finally { setBusy(false) }
  }

  function openNegotiation() {
    return act(async () => {
      const item = await api(`/api/requests/${selectedApplicationId}/negotiation`, { method: 'POST', body: {} })
      setSelectedNegotiationId(item.id)
    }, 'Negociación documental abierta.')
  }

  function addMeeting(event) {
    event.preventDefault(); const value = new FormData(event.currentTarget).get('scheduled_for')
    return act(() => api(`/api/negotiations/${negotiation.id}/meetings`, { method: 'POST', body: { scheduled_for: new Date(value).toISOString() } }), 'Fecha propuesta por Maxim y registrada sin coordinación automática.')
  }

  function addProposal(event) {
    event.preventDefault(); const text = new FormData(event.currentTarget).get('text')
    return act(() => api(`/api/negotiations/${negotiation.id}/proposals`, { method: 'POST', body: { text } }), 'Propuesta no vinculante registrada.')
  }

  function addMessage(event) {
    event.preventDefault(); const data = new FormData(event.currentTarget)
    return act(() => api(`/api/negotiations/${negotiation.id}/messages`, { method: 'POST', body: { recipients: data.get('recipients'), body: data.get('body'), simulate_delivery_failure: false } }), 'Mensaje preservado en negociación.')
  }

  function uploadDocument(event) {
    event.preventDefault(); const data = new FormData(event.currentTarget)
    return act(() => api(`/api/negotiations/${negotiation.id}/documents`, { method: 'POST', body: data }), 'PDF compartido con ambas empresas.')
  }

  return (
    <main className="dashboard" aria-busy={busy}>
      <div className="hero-card broker-hero"><div><p className="eyebrow">Broker · Negotiation facilitator</p><h1>Cada acuerdo, en contexto.</h1><p>Registra lo que las personas proponen. Nunca decide por ellas.</p><p className="microcopy">Maxim: abre la negociación, propone fechas y comparte el PDF del contrato. El crédito y el cronograma los llevan César y Juan Pedro.</p></div><div className="hero-metric"><span>{negotiations.length}</span><small>negociaciones asignadas</small></div></div>
      <Notice {...notice} />
      <div className="two-column">
        <Section eyebrow="Asignación" title="Abrir negociación">
          {applications.length === 0 ? <Empty>Sin solicitudes asignadas.</Empty> : <div className="inline-form"><label>Asignación<select value={selectedApplicationId || ''} onChange={(event) => setSelectedApplicationId(event.target.value)}>{applications.map((item) => <option key={item.application_id} value={item.application_id}>#{item.application_id} · {item.machinery_type}</option>)}</select></label><button className="primary" onClick={openNegotiation}>Abrir o consultar</button></div>}
        </Section>
        <Section eyebrow="Mi cartera" title="Negociaciones">
          {negotiations.length === 0 ? <Empty>No tienes negociaciones asignadas.</Empty> : <div className="stack-list">{negotiations.map((item) => <button className={`list-row ${Number(selectedNegotiationId) === item.id ? 'active' : ''}`} key={item.id} onClick={() => setSelectedNegotiationId(item.id)}><span><strong>Negociación #{item.id}</strong><small>Solicitud #{item.application_id} · última actividad {new Date(item.updated_at).toLocaleString('es-PE')}</small></span><StatusBadge value={item.state} /></button>)}</div>}
        </Section>
      </div>

      {negotiation && <>
        <div className="three-column">
          <Section eyebrow="Fecha" title="Proponer reunión"><form onSubmit={addMeeting} className="stack-form"><label>Fecha y hora<input required name="scheduled_for" type="datetime-local" /></label><button disabled={busy}>Registrar propuesta</button></form></Section>
          <Section eyebrow="Idea" title="Propuesta no vinculante"><form onSubmit={addProposal} className="stack-form"><label>Texto<textarea required minLength="10" name="text" defaultValue="Proponer una gracia inicial alineada al cierre del proyecto." /></label><button disabled={busy}>Registrar idea</button></form></Section>
          <Section eyebrow="Guía" title="Mensaje"><form onSubmit={addMessage} className="stack-form"><label>Destinatarios<select name="recipients"><option>CLIENT</option><option>LEASING</option><option>BOTH</option></select></label><label>Mensaje<textarea required name="body" defaultValue="Revisen el cronograma propuesto antes de confirmar." /></label><button disabled={busy}>Registrar mensaje</button></form></Section>
        </div>
        <Section eyebrow="Contrato" title="PDF, resumen y detalles">
          <form className="document-form" onSubmit={uploadDocument}><label>PDF<input required type="file" name="file" accept="application/pdf,.pdf" /></label><label>Resumen<textarea required minLength="10" name="summary" defaultValue="Contrato de leasing para maquinaria del proyecto." /></label><label>Detalles estructurados<textarea required minLength="2" name="structured_details" defaultValue='{"asset":"excavadora","term_months":12}' /></label><button className="primary" disabled={busy}>Compartir documento</button></form>
          <div className="record-grid"><div><h3>Fechas propuestas</h3>{negotiation.meetings.map((item) => <p key={item.id}>{new Date(item.scheduled_for).toLocaleString('es-PE')} <StatusBadge value={item.state} /></p>)}</div><div><h3>Propuestas</h3>{negotiation.proposals.map((item) => <p key={item.id}>{item.text}</p>)}</div><div><h3>Mensajes</h3>{negotiation.messages.map((item) => <p key={item.id}><strong>{item.recipients}</strong>: {item.body} <StatusBadge value={item.delivery_status} /></p>)}</div></div>
          <div className="record-grid"><div><h3>Documentos compartidos</h3>{negotiation.documents.map((item) => <p key={item.id}><strong>{item.original_name}</strong><br />{item.summary}<br /><button className="ghost" onClick={() => downloadFile(`/api/negotiations/${negotiation.id}/documents/${item.id}/download`, item.original_name)}>Descargar PDF</button></p>)}</div></div>
        </Section>
      </>}
    </main>
  )
}
