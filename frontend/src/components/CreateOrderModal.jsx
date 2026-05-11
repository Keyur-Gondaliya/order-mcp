import { useState } from 'react'
import { api } from '../api'

const emptyItem = () => ({ sku: '', qty: 1, price: '' })

export default function CreateOrderModal({ onCreated, onClose }) {
  const [customer, setCustomer] = useState('')
  const [items, setItems] = useState([emptyItem()])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const updateItem = (idx, field, value) => {
    setItems(prev => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item))
  }

  const addItem = () => setItems(prev => [...prev, emptyItem()])
  const removeItem = (idx) => setItems(prev => prev.filter((_, i) => i !== idx))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    const parsedItems = items.map(i => ({
      sku: i.sku.trim(),
      qty: parseInt(i.qty, 10),
      price: parseFloat(i.price),
    }))
    if (!customer.includes('@')) return setError('Enter a valid email.')
    if (parsedItems.some(i => !i.sku || i.qty < 1 || isNaN(i.price))) {
      return setError('Fill in all item fields correctly.')
    }
    setSubmitting(true)
    try {
      const order = await api.createOrder({ customer, items: parsedItems })
      onCreated(order)
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <h2>New Order</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Customer Email</label>
            <input
              type="email"
              value={customer}
              onChange={e => setCustomer(e.target.value)}
              placeholder="customer@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label>Items</label>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: '0.4rem', marginBottom: '0.35rem', fontSize: '0.78rem', color: '#6b7280' }}>
              <span>SKU</span><span>Qty</span><span>Price</span><span/>
            </div>
            <div className="items-list">
              {items.map((item, idx) => (
                <div className="item-row" key={idx}>
                  <input
                    placeholder="SKU-001"
                    value={item.sku}
                    onChange={e => updateItem(idx, 'sku', e.target.value)}
                    required
                  />
                  <input
                    type="number" min="1" placeholder="1"
                    value={item.qty}
                    onChange={e => updateItem(idx, 'qty', e.target.value)}
                    required
                  />
                  <input
                    type="number" min="0" step="0.01" placeholder="0.00"
                    value={item.price}
                    onChange={e => updateItem(idx, 'price', e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    className="remove-btn"
                    onClick={() => removeItem(idx)}
                    disabled={items.length === 1}
                    title="Remove item"
                  >×</button>
                </div>
              ))}
            </div>
            <button type="button" className="btn btn-sm" onClick={addItem}>+ Add Item</button>
          </div>

          {error && <div className="error-banner">{error}</div>}

          <div className="modal-footer">
            <button type="button" className="btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Creating...' : 'Create Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
