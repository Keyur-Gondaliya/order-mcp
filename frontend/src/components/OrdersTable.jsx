import { useState } from 'react'
import StatusBadge from './StatusBadge'

const TRANSITIONS = {
  pending:   ['paid', 'cancelled'],
  paid:      ['shipped', 'cancelled', 'refunded'],
  shipped:   ['delivered', 'refunded'],
  delivered: ['refunded'],
  cancelled: [],
  refunded:  [],
}

const ACTION_LABELS = {
  paid:      'Mark Paid',
  shipped:   'Mark Shipped',
  delivered: 'Mark Delivered',
  cancelled: 'Cancel',
  refunded:  'Refund',
}

export default function OrdersTable({ orders, onAction }) {
  const [pendingId, setPendingId] = useState(null)

  const handleAction = async (orderId, value) => {
    if (!value) return
    const reason = ['cancel', 'refund'].includes(value)
      ? prompt(`Reason for ${value} (optional):`) ?? ''
      : null
    setPendingId(orderId)
    try {
      if (value === 'cancel') await onAction('cancel', orderId, reason)
      else if (value === 'refund') await onAction('refund', orderId, reason)
      else await onAction('status', orderId, value)
    } finally {
      setPendingId(null)
    }
  }

  if (!orders.length) {
    return (
      <table className="orders-table">
        <thead>
          <tr>
            <th>Order ID</th><th>Customer</th><th>Items</th>
            <th>Total</th><th>Status</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr className="empty-row">
            <td colSpan={6}>No orders found</td>
          </tr>
        </tbody>
      </table>
    )
  }

  return (
    <table className="orders-table">
      <thead>
        <tr>
          <th>Order ID</th>
          <th>Customer</th>
          <th>Items</th>
          <th>Total</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {orders.map(order => {
          const transitions = TRANSITIONS[order.status] ?? []
          return (
            <tr key={order.id}>
              <td className="col-id">{order.id}</td>
              <td className="col-customer">{order.customer}</td>
              <td className="col-skus">
                {order.items.map(i => `${i.sku} ×${i.qty}`).join(', ')}
              </td>
              <td className="col-total">${order.total.toFixed(2)}</td>
              <td><StatusBadge status={order.status} /></td>
              <td>
                {transitions.length > 0 ? (
                  <select
                    className="action-select"
                    defaultValue=""
                    disabled={pendingId === order.id}
                    onChange={e => { handleAction(order.id, e.target.value); e.target.value = '' }}
                  >
                    <option value="" disabled>Action…</option>
                    {transitions.map(t => (
                      <option key={t} value={t === 'cancelled' ? 'cancel' : t === 'refunded' ? 'refund' : t}>
                        {ACTION_LABELS[t]}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span style={{ color: 'var(--text-3)', fontSize: '0.85rem' }}>—</span>
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
