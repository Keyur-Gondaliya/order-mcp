import { useState, useEffect, useCallback } from 'react'
import { api } from './api'
import OrdersTable from './components/OrdersTable'
import CreateOrderModal from './components/CreateOrderModal'
import './App.css'

const STATUSES = ['pending', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded']

export default function App() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [filters, setFilters] = useState({ customer: '', status: '' })

  const fetchOrders = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getOrders(filters)
      setOrders(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { fetchOrders() }, [fetchOrders])

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

  const handleCreated = (order) => {
    setOrders(prev => [order, ...prev])
    setShowCreate(false)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Order Management</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          + New Order
        </button>
      </header>

      <div className="filters">
        <input
          type="text"
          placeholder="Filter by customer email"
          value={filters.customer}
          onChange={e => setFilters(f => ({ ...f, customer: e.target.value }))}
        />
        <select
          value={filters.status}
          onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}
        >
          <option value="">All statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <button className="btn" onClick={fetchOrders}>Refresh</button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="loading">Loading orders...</div>
      ) : (
        <OrdersTable orders={orders} onAction={handleOrderAction} />
      )}

      {showCreate && (
        <CreateOrderModal onCreated={handleCreated} onClose={() => setShowCreate(false)} />
      )}
    </div>
  )
}
