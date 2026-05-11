import { useState } from 'react'
import { api } from '../api'

const emptyItem = () => ({ sku: '', qty: 1, price: '' })

export default function CreateOrderModal({ onCreated, onClose }) {
  const [customer, setCustomer] = useState('')
  const [items, setItems] = useState([emptyItem()])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const updateItem = (idx, field, value) =>
    setItems(prev => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    const parsed = items.map(i => ({
      sku: i.sku.trim(),
      qty: parseInt(i.qty, 10),
      price: parseFloat(i.price),
    }))
    if (!customer.includes('@')) return setError('Enter a valid email address.')
    if (parsed.some(i => !i.sku || i.qty < 1 || isNaN(i.price))) {
      return setError('Fill in all item fields correctly.')
    }
    setSubmitting(true)
    try {
      onCreated(await api.createOrder({ customer, items: parsed }))
    } catch (e) {
      setError(e.message)
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2>New Order</h2>
          <button className="modal-close" onClick={onClose} title="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Customer Email</label>
            <input
              className="form-input"
              type="email"
              value={customer}
              onChange={e => setCustomer(e.target.value)}
              placeholder="customer@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Items</label>
            <div className="items-header">
              <span>SKU</span><span>Qty</span><span>Price ($)</span><span/>
            </div>
            <div className="items-list">
              {items.map((item, idx) => (
                <div className="item-row" key={idx}>
                  <input className="form-input" placeholder="SKU-001" value={item.sku}
                    onChange={e => updateItem(idx, 'sku', e.target.value)} required />
                  <input className="form-input" type="number" min="1" placeholder="1" value={item.qty}
                    onChange={e => updateItem(idx, 'qty', e.target.value)} required />
                  <input className="form-input" type="number" min="0" step="0.01" placeholder="0.00" value={item.price}
                    onChange={e => updateItem(idx, 'price', e.target.value)} required />
                  <button type="button" className="remove-btn" onClick={() => setItems(prev => prev.filter((_, i) => i !== idx))}
                    disabled={items.length === 1} title="Remove">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>
                </div>
              ))}
            </div>
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => setItems(prev => [...prev, emptyItem()])}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              Add Item
            </button>
          </div>

          {error && <div className="error-banner" style={{ marginBottom: '0.75rem' }}>{error}</div>}

          <div className="modal-footer">
            <button type="button" className="btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Creating…' : 'Create Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
