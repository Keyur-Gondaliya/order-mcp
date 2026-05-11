import { useState, useEffect, useCallback } from 'react'
import { api } from './api'
import OrdersTable from './components/OrdersTable'
import CreateOrderModal from './components/CreateOrderModal'
import ApiAccess from './components/ApiAccess'
import './App.css'

const STATUSES = ['pending', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded']

export default function App() {
  const [tab, setTab] = useState('orders')
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [filters, setFilters] = useState({ customer: '', status: '' })

  const fetchOrders = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setOrders(await api.getOrders(filters))
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { if (tab === 'orders') fetchOrders() }, [fetchOrders, tab])

  const handleOrderAction = async (action, orderId, payload) => {
    try {
      let updated
      if (action === 'status') updated = await api.updateStatus(orderId, payload)
      else if (action === 'cancel') updated = await api.cancelOrder(orderId, payload)
      else if (action === 'refund') updated = await api.refundOrder(orderId, payload)
      setOrders(prev => prev.map(o => o.id === orderId ? updated : o))
    } catch (e) {
      alert(e.message)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-left">
          <div className="app-logo">
            <div className="app-logo-mark">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
                <line x1="3" y1="6" x2="21" y2="6"/>
                <path d="M16 10a4 4 0 0 1-8 0"/>
              </svg>
            </div>
            <span className="app-title">OrderMCP</span>
          </div>
          <nav className="app-nav">
            <button className={`nav-tab${tab === 'orders' ? ' nav-tab-active' : ''}`} onClick={() => setTab('orders')}>
              Orders
            </button>
            <button className={`nav-tab${tab === 'api' ? ' nav-tab-active' : ''}`} onClick={() => setTab('api')}>
              API Access
            </button>
          </nav>
        </div>
        {tab === 'orders' && (
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            New Order
          </button>
        )}
      </header>

      {tab === 'api' ? (
        <ApiAccess />
      ) : (
        <>
          <div className="toolbar">
            <div className="toolbar-filters">
              <input
                className="input input-email"
                type="text"
                placeholder="Filter by customer email…"
                value={filters.customer}
                onChange={e => setFilters(f => ({ ...f, customer: e.target.value }))}
              />
              <select
                className="input input-select"
                value={filters.status}
                onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}
              >
                <option value="">All statuses</option>
                {STATUSES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
            </div>
            <button className="btn" onClick={fetchOrders}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
              Refresh
            </button>
          </div>

          {error && <div className="error-banner">{error}</div>}

          {loading ? (
            <div className="loading">Loading…</div>
          ) : (
            <div className="table-wrap">
              <OrdersTable orders={orders} onAction={handleOrderAction} />
            </div>
          )}
        </>
      )}

      {showCreate && (
        <CreateOrderModal
          onCreated={order => { setOrders(prev => [order, ...prev]); setShowCreate(false) }}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  )
}
