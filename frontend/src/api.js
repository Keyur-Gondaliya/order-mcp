const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Request failed')
  return data
}

export const api = {
  getOrders: (params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
    ).toString()
    return request(`/orders${qs ? `?${qs}` : ''}`)
  },
  getOrder: (id) => request(`/orders/${id}`),
  createOrder: (body) => request('/orders', { method: 'POST', body }),
  updateStatus: (id, status) =>
    request(`/orders/${id}/status`, { method: 'PATCH', body: { status } }),
  cancelOrder: (id, reason = '') =>
    request(`/orders/${id}/cancel`, { method: 'POST', body: { reason } }),
  refundOrder: (id, reason = '') =>
    request(`/orders/${id}/refund`, { method: 'POST', body: { reason } }),

  getToken: () => request('/auth/token'),
  regenerateToken: () => request('/auth/token/regenerate', { method: 'POST' }),
  revokeToken: () => request('/auth/token', { method: 'DELETE' }),
}
