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

export default function OrdersTable({ orders, onAction }) {
  const [pendingId, setPendingId] = useState(null)

  const handleAction = async (orderId, value, currentStatus) => {
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
        <thead><tr>
          <th>Order ID</th><th>Customer</th><th>Items</th>
          <th>Total</th><th>Status</th><th>Actions</th>
        </tr></thead>
        <tbody><tr className="empty-row"><td colSpan={6}>No orders found</td></tr></tbody>
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
              <td><code>{order.id}</code></td>
              <td>{order.customer}</td>
              <td className="items-cell">
                {order.items.map(i => `${i.sku} ×${i.qty}`).join(', ')}
              </td>
              <td>${order.total.toFixed(2)}</td>
              <td><StatusBadge status={order.status} /></td>
              <td className="actions-cell">
                {transitions.length > 0 ? (
                  <select
                    className="action-select"
                    defaultValue=""
                    disabled={pendingId === order.id}
                    onChange={e => {
                      handleAction(order.id, e.target.value, order.status)
                      e.target.value = ''
                    }}
                  >
                    <option value="" disabled>Action...</option>
                    {transitions.includes('paid')      && <option value="paid">Mark Paid</option>}
                    {transitions.includes('shipped')   && <option value="shipped">Mark Shipped</option>}
                    {transitions.includes('delivered') && <option value="delivered">Mark Delivered</option>}
                    {transitions.includes('cancelled') && <option value="cancel">Cancel</option>}
                    {transitions.includes('refunded')  && <option value="refund">Refund</option>}
                  </select>
                ) : (
                  <span style={{ color: '#9ca3af', fontSize: '0.8rem' }}>—</span>
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
