import React from 'react'

export function StatusBadge({ value }) {
  const normalized = String(value || 'UNKNOWN').toLowerCase().replaceAll('_', '-')
  return <span className={`badge badge-${normalized}`}>{String(value || 'Unknown').replaceAll('_', ' ')}</span>
}

export function Notice({ error, success }) {
  if (!error && !success) return null
  return <div role={error ? 'alert' : 'status'} className={`notice ${error ? 'notice-error' : 'notice-success'}`}>{error || success}</div>
}

export function Empty({ children }) {
  return <div className="empty-state"><span>◇</span><p>{children}</p></div>
}

export function Money({ amount, currency = 'PEN' }) {
  const value = Number(amount || 0)
  return <>{new Intl.NumberFormat('es-PE', { style: 'currency', currency }).format(value)}</>
}

export function Section({ eyebrow, title, children, actions }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div>
        {actions && <div className="panel-actions">{actions}</div>}
      </div>
      {children}
    </section>
  )
}
