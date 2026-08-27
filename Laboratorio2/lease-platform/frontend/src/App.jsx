import { useEffect, useState } from 'react'
import { hasToken, sessionApi, setToken } from './api/client'
import ClientView from './views/ClientView'
import LeasingView from './views/LeasingView'
import BrokerView from './views/BrokerView'
import './styles/theme.css'

export default function App() {
  const [users, setUsers] = useState([])
  const [current, setCurrent] = useState(null)
  const [error, setError] = useState('')
  const [restoring, setRestoring] = useState(hasToken())

  useEffect(() => { sessionApi.users().then(setUsers).catch((reason) => setError(reason.message)) }, [])

  useEffect(() => {
    if (!hasToken()) { setRestoring(false); return }
    sessionApi.me().then(setCurrent).catch(() => setToken('')).finally(() => setRestoring(false))
  }, [])

  async function selectUser(userId) {
    try {
      const selected = await sessionApi.select(Number(userId))
      setToken(selected.access_token)
      setCurrent(selected.user)
      setError('')
    } catch (reason) { setError(reason.message) }
  }

  function logout() { setToken(''); setCurrent(null) }

  if (restoring) return <div className="login-shell" aria-busy="true" />

  if (!current) return (
    <div className="login-shell">
      <div className="ambient ambient-one" /><div className="ambient ambient-two" />
      <main className="login-card">
        <div className="brand-mark">L<span>$</span></div>
        <p className="eyebrow">Lea$e · Phase 1 POC</p>
        <h1>Financing,<br /><em>made clear.</em></h1>
        <p className="login-copy">Elige una identidad demo. Cada vista aplica permisos reales en el backend, sin fingir autenticación productiva.</p>
        {error && <div role="alert" className="notice notice-error">{error}</div>}
        <div className="identity-grid">{users.map((user) => <button key={user.id} onClick={() => selectUser(user.id)} className="identity-card"><span className={`avatar avatar-${user.role.toLowerCase()}`}>{user.name.charAt(0)}</span><span><strong>{user.name.split(' — ')[0]}</strong><small>{user.name.split(' — ')[1]}<br />{user.organization}</small></span><b>→</b></button>)}</div>
        <div className="scope-footer"><span>✓ Sin proveedor</span><span>✓ Sin decisión crediticia interna</span><a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">Swagger UI ↗</a></div>
      </main>
    </div>
  )

  return <div className="app-shell">
    <header className="topbar"><a className="wordmark" href="/">Lea<span>$</span>e</a><div className="topbar-scope">POC · {current.role}</div><div className="current-user"><span className={`avatar avatar-${current.role.toLowerCase()}`}>{current.name.charAt(0)}</span><span><strong>{current.name.split(' — ')[0]}</strong><small>{current.organization}</small></span><button className="text-button" onClick={logout}>Cambiar rol</button></div></header>
    {current.role === 'CLIENT' && <ClientView user={current} />}
    {current.role === 'LEASING' && <LeasingView user={current} />}
    {current.role === 'BROKER' && <BrokerView user={current} />}
  </div>
}

