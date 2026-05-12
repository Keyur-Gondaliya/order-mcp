import { useState } from 'react'
import { api } from '../api'
import './ApiAccess.css'

const MCP_HOST = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host

function mcpConfig(token) {
  return JSON.stringify(
    {
      mcpServers: {
        'order-system': {
          type: 'http',
          url: `http://${MCP_HOST}/mcp`,
          headers: { Authorization: `Bearer ${token}` },
        },
      },
    },
    null,
    2
  )
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button className="copy-btn" onClick={handleCopy} title="Copy">
      {copied ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      )}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

export default function ApiAccess({ token: initialToken, onTokenChange, onLogout }) {
  const [token, setToken] = useState(initialToken)
  const [showToken, setShowToken] = useState(false)
  const [confirming, setConfirming] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleRegenerate = async () => {
    if (confirming !== 'regenerate') { setConfirming('regenerate'); return }
    setConfirming(null)
    setLoading(true)
    try {
      const d = await api.regenerateToken()
      setToken(d.token)
      onTokenChange(d.token)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRevoke = async () => {
    if (confirming !== 'revoke') { setConfirming('revoke'); return }
    setConfirming(null)
    setLoading(true)
    try {
      await api.revokeToken()
      onLogout()
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }

  const maskedToken = token ? token.slice(0, 8) + '•'.repeat(token.length - 8) : ''
  const oauthCmd = `claude mcp add order-system -t http http://${MCP_HOST}/mcp`

  return (
    <div className="api-access">
      <h2 className="api-access-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        API Access &amp; MCP Configuration
      </h2>

      {error && <div className="api-error">{error}</div>}

      {/* Token section */}
      <section className="api-card">
        <div className="api-card-label">Your API Token</div>
        {loading ? (
          <div className="api-loading">Loading…</div>
        ) : token ? (
          <>
            <div className="token-row">
              <input
                className="token-input"
                type={showToken ? 'text' : 'password'}
                readOnly
                value={token}
              />
              <button className="icon-btn" onClick={() => setShowToken(v => !v)} title={showToken ? 'Hide' : 'Show'}>
                {showToken ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                )}
              </button>
              <CopyButton text={token} />
            </div>
            <p className="token-hint">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              Keep this token secret. It provides full access to your business's orders via the API and MCP.
            </p>
            <div className="token-actions">
              <button
                className={`btn-outline${confirming === 'regenerate' ? ' btn-confirm' : ''}`}
                onClick={handleRegenerate}
              >
                {confirming === 'regenerate' ? 'Confirm Regenerate?' : '↻ Regenerate Token'}
              </button>
              <button
                className={`btn-outline btn-danger${confirming === 'revoke' ? ' btn-confirm' : ''}`}
                onClick={handleRevoke}
              >
                {confirming === 'revoke' ? 'Confirm Revoke?' : '✕ Revoke Token'}
              </button>
              {confirming && (
                <button className="btn-ghost-sm" onClick={() => setConfirming(null)}>Cancel</button>
              )}
            </div>
          </>
        ) : (
          <div className="token-revoked">
            <span>Token has been revoked. Sign in again to get a new token.</span>
            <button className="btn-primary-sm" onClick={onLogout}>Sign Out</button>
          </div>
        )}
      </section>

      {/* MCP section */}
      <section className="api-card">
        <div className="api-card-label">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
          Connect via MCP (Model Context Protocol)
        </div>
        <p className="api-card-desc">Add this to your Claude Code settings or MCP configuration file:</p>
        <div className="code-block-wrapper">
          <pre className="code-block">{token ? mcpConfig(token) : mcpConfig('<your-token>')}</pre>
          <CopyButton text={token ? mcpConfig(token) : mcpConfig('<your-token>')} />
        </div>
      </section>

      {/* OAuth section */}
      <section className="api-card">
        <div className="api-card-label-row">
          <div className="api-card-label">Connect via OAuth</div>
          <span className="badge-easier">Easier</span>
        </div>
        <p className="api-card-desc">No config file needed — just run this command:</p>
        <div className="code-block-wrapper code-block-single">
          <code className="code-inline">{oauthCmd}</code>
          <CopyButton text={oauthCmd} />
        </div>
        <p className="oauth-hint">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          Opens your browser to sign in, then you're connected.
        </p>
      </section>
    </div>
  )
}
