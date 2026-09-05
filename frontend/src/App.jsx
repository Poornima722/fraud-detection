import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = 'http://127.0.0.1:5000'

const initialForm = {
  customer_id: 'C003', dob: '', transaction_time: '2026-09-04T14:32', amount: 1200,
  merchant: 'Urban Market', category: 'grocery_pos', gender: 'F', city: 'Bengaluru', state: 'Karnataka',
  zip: 560001, lat: 12.9716, long: 77.5946, city_pop: 10000000, merch_lat: 12.9616, merch_long: 77.6046,
}
const presets = {
  normal: initialForm,

  suspicious: {
    ...initialForm,
    customer_id: 'C001',
    transaction_time: '2026-09-04T03:17',
    amount: 4850,
    merchant: 'Luxury Electronics Hub',
    category: 'shopping_net',
    city: 'Mumbai',
    state: 'Maharashtra',
    zip: 400001,
    lat: 19.076,
    long: 72.8777,
    merch_lat: 19.2183,
    merch_long: 72.9781,
  },

  highRisk: {
    ...initialForm,
    customer_id: 'C001',
    transaction_time: '2026-09-04T03:18',
    amount: 125009,
    merchant: 'Luxury Electronics Hub',
    category: 'shopping_net',
    city: 'Mumbai',
    state: 'Maharashtra',
    zip: 400001,
    lat: 19.076,
    long: 72.8777,
    merch_lat: 19.2183,
    merch_long: 72.9781,
  },
}
const fields = [
  ['customer_id', 'Customer ID', 'text'], ['dob', 'Date of Birth', 'date'], ['transaction_time', 'Transaction Time', 'datetime-local'], ['amount', 'Amount', 'number'],
  ['merchant', 'Merchant', 'text'], ['category', 'Category', 'text'], ['gender', 'Gender', 'text'], ['city', 'City', 'text'],
  ['state', 'State', 'text'], ['zip', 'ZIP', 'number'], ['lat', 'Latitude', 'number'], ['long', 'Longitude', 'number'],
  ['city_pop', 'City Population', 'number'], ['merch_lat', 'Merchant Latitude', 'number'], ['merch_long', 'Merchant Longitude', 'number'],
]
const operationalAction = (risk) => ({ LOW: 'ALLOW', MEDIUM: 'REVIEW', HIGH: 'BLOCK' }[risk] || 'REVIEW')
const numericFields = new Set(['amount', 'zip', 'lat', 'long', 'city_pop', 'merch_lat', 'merch_long'])
const formatMetric = (value) => `${(Number(value) * 100).toFixed(2)}%`

function App() {
  const [form, setForm] = useState(initialForm)
  const [assessment, setAssessment] = useState(null)
  const [audit, setAudit] = useState([])
  const [modelPerformance, setModelPerformance] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isLoadingAudit, setIsLoadingAudit] = useState(true)
  const [isLoadingPerformance, setIsLoadingPerformance] = useState(true)
  const [isRecording, setIsRecording] = useState(false)
  const [isResolvingCallback, setIsResolvingCallback] = useState(false)
  const [error, setError] = useState('')
  const [decisionMessage, setDecisionMessage] = useState(null)

  async function loadAudit() {
    setIsLoadingAudit(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/audit`)
      if (!response.ok) throw new Error('Unable to load audit activity.')
      const data = await response.json()
      setAudit(Array.isArray(data) ? data : data.audit || data.decisions || [])
    } catch (requestError) { setError(requestError.message) } finally { setIsLoadingAudit(false) }
  }
  async function loadModelPerformance() {
    setIsLoadingPerformance(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/model-performance`)
      if (!response.ok) throw new Error('Unable to load model performance.')
      setModelPerformance(await response.json())
    } catch (requestError) { setError(requestError.message) } finally { setIsLoadingPerformance(false) }
  }
  useEffect(() => { Promise.resolve().then(() => { loadAudit(); loadModelPerformance() }) }, [])
  function updateField(event) { setForm((current) => ({ ...current, [event.target.name]: event.target.value })) }
  function applyPreset(preset) { setForm({ ...preset }); setAssessment(null); setDecisionMessage(null); setError('') }

  async function analyzeTransaction(event) {
    event.preventDefault(); setIsAnalyzing(true); setError(''); setAssessment(null); setDecisionMessage(null)
    try {
      const payload = Object.fromEntries(
        Object.entries(form).map(([key, value]) => [
          key,
          numericFields.has(key) ? Number(value) : value,
        ])
      )

      payload.transaction_time = `${form.transaction_time}:00+05:30`

      const response = await fetch(`${API_BASE_URL}/api/transactions/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        let errorMessage
        try {
          const errorBody = await response.json()
          errorMessage = errorBody?.error
        } catch {
          errorMessage = undefined
        }
        throw new Error(errorMessage || 'Analysis failed. Check that the risk service is online.')
      }
      setAssessment(await response.json())
    } catch (requestError) { setError(requestError.message) } finally { setIsAnalyzing(false) }
  }
  async function recordDecision(action) {
    if (!assessment?.transaction_id) return
    setIsRecording(true); setError('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/transactions/${assessment.transaction_id}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action }) })
      if (!response.ok) {
        let errorMessage
        try { errorMessage = (await response.json())?.error } catch { errorMessage = undefined }
        throw new Error(errorMessage || 'The analyst decision could not be recorded.')
      }
      const result = await response.json()
      setDecisionMessage({ action, status: result.status, message: result.message, timestamp: result.timestamp || result.recorded_at }); loadAudit()
    } catch (requestError) { setError(requestError.message) } finally { setIsRecording(false) }
  }
  async function resolveCallback(outcome) {
    if (!assessment?.transaction_id) return
    setIsResolvingCallback(true); setError('')
    try {
      const endpoint = outcome === 'success' ? 'otp-success' : 'otp-failure'
      const response = await fetch(`${API_BASE_URL}/api/transactions/${assessment.transaction_id}/${endpoint}`, { method: 'POST' })
      const result = await response.json()
      if (!response.ok) throw new Error(result?.error || 'The customer callback could not be recorded.')
      setDecisionMessage({ action: result.action, status: result.status, message: result.message })
      loadAudit()
    } catch (requestError) { setError(requestError.message) } finally { setIsResolvingCallback(false) }
  }
  const riskLevel = assessment?.risk_level?.toUpperCase()
  const probability = assessment ? `${(Number(assessment.fraud_probability) * 100).toFixed(2)}%` : null
  const transactionStatus = decisionMessage?.status === 'blocked' ? 'BLOCKED' : decisionMessage?.status === 'approved' ? 'APPROVED' : decisionMessage?.status === 'awaiting_verification' ? 'AWAITING VERIFICATION' : riskLevel === 'LOW' ? 'AUTO-ALLOWED' : riskLevel === 'HIGH' ? 'AUTO-BLOCKED' : riskLevel === 'MEDIUM' ? 'AWAITING ANALYST' : null

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand-lockup"><div className="brand-mark" aria-hidden="true"><span>⌁</span></div><div><p className="eyebrow">SECURITY OPERATIONS</p><h1>AI Risk Manager</h1><p className="subtitle">Transaction Fraud Detection &amp; Investigation</p></div></div>
      <div className="system-status"><span className="status-dot" /> SYSTEM ONLINE</div>
      <div className="policy"><span>RISK POLICY</span><strong>&lt;25% ALLOW</strong><i /><strong>25–78% REVIEW</strong><i /><strong>≥78% BLOCK</strong></div>
    </header>
    <section className="workspace-grid">
      <section className="panel transaction-panel"><div className="section-heading"><div><span className="section-index">01</span><h2>New transaction</h2></div><span className="live-tag">LIVE CHECK</span></div><p className="panel-intro">Run a transaction through the fraud detection model.</p>
        <div className="preset-row"><span>QUICK DEMO</span><button type="button" onClick={() => applyPreset(presets.normal)}>Normal Transaction</button><button type="button" onClick={() => applyPreset(presets.suspicious)}>Suspicious Spike</button><button type="button" onClick={() => applyPreset(presets.highRisk)}>High-Risk Scenario</button></div>
        <form onSubmit={analyzeTransaction}><div className="form-grid">{fields.map(([name, label, type]) => <label className={name === 'transaction_time' || name === 'merchant' ? 'wide-field' : ''} key={name}><span>{label}</span><input name={name} type={type} value={form[name]} onChange={updateField} step={type === 'number' ? 'any' : undefined} required={name !== 'dob'} /></label>)}</div>{error && <p className="error-message" role="alert">{error}</p>}<button className="analyze-button" type="submit" disabled={isAnalyzing}>{isAnalyzing ? <><span className="spinner" /> ANALYZING TRANSACTION</> : <>ANALYZE TRANSACTION <span>→</span></>}</button></form>
      </section>
      <section className={`panel assessment-panel ${riskLevel ? `risk-${riskLevel.toLowerCase()}` : ''}`}><div className="section-heading"><div><span className="section-index">02</span><h2>Risk assessment</h2></div><span className="assessment-code">MODEL OUTPUT</span></div>
        {!assessment ? <div className="empty-assessment"><div className="scan-icon">◎</div><p>Submit a transaction to begin risk analysis.</p><span>Results from the live model will appear here.</span></div> : <div className="assessment-content"><div className="risk-banner"><div><span className="metric-label">RISK LEVEL</span><strong>{riskLevel}</strong></div><div className="probability"><span className="metric-label">FRAUD PROBABILITY</span><strong>{probability}</strong></div></div><div className="assessment-stats"><div><span>OPERATIONAL ACTION</span><strong>{operationalAction(riskLevel)}</strong></div><div><span>MODEL DECISION</span><strong>{assessment.decision}</strong></div><div><span>TRANSACTION STATUS</span><strong>{transactionStatus || 'AWAITING ANALYST'}</strong></div><div><span>TRANSACTION ID</span><strong className="transaction-id">{assessment.transaction_id}</strong></div></div><div className="evidence"><h3>Why this transaction?</h3><p className="decision-reason">{assessment.decision_reason}</p>{assessment.evidence?.length ? <ul>{assessment.evidence.map((item, index) => <li key={`${item}-${index}`}><span>+</span>{item}</li>)}</ul> : <p className="muted">No evidence returned by the model.</p>}</div>{riskLevel === 'MEDIUM' && !decisionMessage && <div className="action-required"><div><h3>Analyst console</h3><p>Record an analyst decision for this review.</p></div><div className="decision-buttons"><button type="button" onClick={() => recordDecision('APPROVE')} disabled={isRecording}>APPROVE</button><button type="button" onClick={() => recordDecision('TRIGGER_OTP')} disabled={isRecording}>TRIGGER STEP-UP CHALLENGE</button><button type="button" onClick={() => recordDecision('BLOCK')} disabled={isRecording}>BLOCK</button></div></div>}{decisionMessage?.status === 'awaiting_verification' && <div className="otp-simulation"><div><h3>CHALLENGE DISPATCHED — AWAITING CARDHOLDER VERIFICATION</h3></div><div className="callback-simulator"><span>DEMO SIMULATOR: MOCK CUSTOMER CALLBACK</span><div><button type="button" onClick={() => resolveCallback('success')} disabled={isResolvingCallback}>Simulate Customer Passed OTP</button><button type="button" onClick={() => resolveCallback('failure')} disabled={isResolvingCallback}>Simulate Customer Failed / Expired</button></div></div></div>}{decisionMessage && decisionMessage.status !== 'awaiting_verification' && <div className={`decision-success decision-${decisionMessage.status}`}><span>{decisionMessage.status === 'approved' ? '✓' : '✕'}</span><div><strong>{decisionMessage.status === 'approved' ? (decisionMessage.message ? 'OTP VERIFIED' : 'Transaction APPROVED') : (decisionMessage.message ? 'OTP FAILED / EXPIRED' : 'Transaction BLOCKED')}</strong><p>Transaction {decisionMessage.status === 'approved' ? 'APPROVED' : 'BLOCKED'}</p>{decisionMessage.timestamp && <p>Timestamp: {decisionMessage.timestamp}</p>}</div></div>}</div>}
      </section>
    </section>
    <section className="model-performance"><div className="section-heading"><div><span className="section-index">03</span><h2>Model performance</h2></div><span className="assessment-code">EVALUATION SET</span></div>{isLoadingPerformance ? <p className="table-state">Calculating evaluation metrics...</p> : !modelPerformance ? <p className="table-state">Model performance is unavailable.</p> : <><div className="performance-metrics"><div><span>PRECISION</span><strong>{formatMetric(modelPerformance.precision)}</strong></div><div><span>RECALL</span><strong>{formatMetric(modelPerformance.recall)}</strong></div><div><span>F1 SCORE</span><strong>{formatMetric(modelPerformance.f1_score)}</strong></div><div><span>FALSE POSITIVE RATE</span><strong>{formatMetric(modelPerformance.false_positive_rate)}</strong></div></div><div className="performance-meta"><span>Evaluation threshold: <strong>{modelPerformance.threshold.toFixed(2)}</strong></span><span>Evaluation set: <strong>{modelPerformance.evaluation_set}</strong> ({modelPerformance.sample_count.toLocaleString()} rows)</span></div><div className="confusion-matrix"><span>CONFUSION MATRIX</span><div><span>TN <strong>{modelPerformance.confusion_matrix.true_negatives.toLocaleString()}</strong></span><span>FP <strong>{modelPerformance.confusion_matrix.false_positives.toLocaleString()}</strong></span><span>FN <strong>{modelPerformance.confusion_matrix.false_negatives.toLocaleString()}</strong></span><span>TP <strong>{modelPerformance.confusion_matrix.true_positives.toLocaleString()}</strong></span></div></div></>}</section>
    <section className="audit-section"><div className="audit-heading"><div><span className="section-index">04</span><h2>Recent audit activity</h2></div><button type="button" className="refresh-button" onClick={loadAudit} disabled={isLoadingAudit}>↻ Refresh</button></div><div className="audit-table-wrap"><table><thead><tr><th>Transaction ID</th><th>Risk Level</th><th>Action</th><th>Time</th></tr></thead><tbody>{isLoadingAudit ? <tr><td colSpan="4" className="table-state">Loading audit activity...</td></tr> : audit.length === 0 ? <tr><td colSpan="4" className="table-state">No analyst decisions recorded yet.</td></tr> : audit.map((item, index) => <tr key={item.transaction_id || index}><td className="transaction-id">{item.transaction_id || item.id || '—'}</td><td><span className={`risk-pill risk-pill-${String(item.risk_level || '').toLowerCase()}`}>{item.risk_level || '—'}</span></td><td>{item.action || item.decision || '—'}</td><td>{item.timestamp || item.created_at || item.time || '—'}</td></tr>)}</tbody></table></div></section>
    <footer><span>AI RISK MANAGER</span><span>ANALYST CONSOLE <b>•</b> v1.0</span></footer>
  </main>
}
export default App
