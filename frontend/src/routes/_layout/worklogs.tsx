import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'

export const Route = createFileRoute('/_layout/worklogs')({
  component: WorklogsPage,
})

function WorklogsPage() {
  const axios = require('axios').default
  axios.defaults.baseURL = 'http://localhost:8000'

  const [allData, setAllData] = useState<any[]>([])
  const [fls, setFls] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Pagination
  const [page, setPage] = useState(1)
  const pageSize = 5 // Small page size to demonstrate pagination

  // Filters
  const [af, setAf] = useState<string>('date') // active filter tab
  const [sd, setSd] = useState('')
  const [ed, setEd] = useState('')
  const [sf, setSf] = useState<number | null>(null) // selected freelancer
  const [st, setSt] = useState<string>('') // selected status

  const [sel, setSel] = useState<number[]>([])
  const [showRev, setShowRev] = useState(false)

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      setLoading(true)
      const [wlsRes, flsRes] = await Promise.all([
        axios.get('http://localhost:8000/api/v1/worklog/worklogs'),
        axios.get('http://localhost:8000/api/v1/worklog/freelancers')
      ])
      setAllData(wlsRes.data)
      setFls(flsRes.data)
      setLoading(false)
    } catch (err) {
      setError('Failed to load data. Please ensure the backend is running.')
      console.error(err)
      setLoading(false)
    }
  }

  const applyFilters = async () => {
    try {
      setLoading(true)
      let url = 'http://localhost:8000/api/v1/worklog/worklogs?'
      if (sd) url += `sd=${sd}&`
      if (ed) url += `ed=${ed}&`
      if (sf) url += `f_id=${sf}&`
      if (st) url += `st=${st}&`

      const res = await axios.get(url)
      setAllData(res.data)
      setPage(1)
      setLoading(false)
    } catch (err) {
      setError('Failed to apply filters.')
      setLoading(false)
    }
  }

  const resetFilters = () => {
    setSd('')
    setEd('')
    setSf(null)
    setSt('')
    loadInitialData()
  }

  const toggleSel = (id: number) => {
    setSel(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const procPay = async () => {
    try {
      await axios.post('http://localhost:8000/api/v1/worklog/payments', {
        worklog_ids: sel,
        start_date: sd || new Date().toISOString(),
        end_date: ed || new Date().toISOString(),
      })
      alert('Payment processed successfully!')
      setSel([])
      setShowRev(false)
      loadInitialData()
    } catch (err) {
      alert('Failed to process payment.')
    }
  }

  if (loading) return (
    <div style={{ padding: '100px', textAlign: 'center' }}>
      <div style={{ fontSize: '24px', fontWeight: '600', color: '#667eea', animation: 'pulse 2s infinite' }}>Loading Assets...</div>
    </div>
  )

  if (error) return (
    <div style={{ padding: '100px', textAlign: 'center' }}>
      <div style={{ color: '#e74c3c', fontSize: '18px' }}>{error}</div>
      <button onClick={loadInitialData} style={{ marginTop: '20px', padding: '10px 20px', cursor: 'pointer' }}>Retry</button>
    </div>
  )

  const displayed = allData.slice((page - 1) * pageSize, page * pageSize)
  const selWls = allData.filter(w => sel.includes(w.id))
  const ttlAmt = selWls.reduce((s, w) => s + (w.ttl || 0), 0)

  return (
    <div style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        padding: '60px 40px',
        borderRadius: '24px',
        marginBottom: '40px',
        color: 'white',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
      }}>
        <h1 style={{ margin: '0 0 12px 0', fontSize: '42px', fontWeight: '800', letterSpacing: '-0.025em' }}>
          Finance Hub
        </h1>
        <p style={{ margin: 0, fontSize: '18px', opacity: 0.7, fontWeight: '400' }}>
          Manage your freelancer settlements and work logs from a single interface.
        </p>
      </div>

      {/* Tabs Filter Section */}
      <div style={{
        background: '#fff',
        borderRadius: '20px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        padding: '24px',
        marginBottom: '32px',
        border: '1px solid #f1f5f9'
      }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid #f1f5f9', paddingBottom: '16px' }}>
          <button
            onClick={() => setAf('date')}
            style={{
              padding: '10px 20px',
              borderRadius: '10px',
              border: 'none',
              background: af === 'date' ? '#f1f5f9' : 'transparent',
              color: af === 'date' ? '#0f172a' : '#64748b',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            📅 Date Range
          </button>
          <button
            onClick={() => setAf('freelancer')}
            style={{
              padding: '10px 20px',
              borderRadius: '10px',
              border: 'none',
              background: af === 'freelancer' ? '#f1f5f9' : 'transparent',
              color: af === 'freelancer' ? '#0f172a' : '#64748b',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            👤 Freelancer
          </button>
          <button
            onClick={() => setAf('status')}
            style={{
              padding: '10px 20px',
              borderRadius: '10px',
              border: 'none',
              background: af === 'status' ? '#f1f5f9' : 'transparent',
              color: af === 'status' ? '#0f172a' : '#64748b',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            ⚡ Status
          </button>
        </div>

        <div style={{ minHeight: '80px', display: 'flex', alignItems: 'flex-end', gap: '16px' }}>
          {af === 'date' && (
            <div style={{ display: 'flex', gap: '16px', flex: 1 }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', marginBottom: '8px', display: 'block' }}>Start</label>
                <input type="datetime-local" value={sd} onChange={e => setSd(e.target.value)} style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #e2e8f0' }} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', marginBottom: '8px', display: 'block' }}>End</label>
                <input type="datetime-local" value={ed} onChange={e => setEd(e.target.value)} style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #e2e8f0' }} />
              </div>
            </div>
          )}
          {af === 'freelancer' && (
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', marginBottom: '8px', display: 'block' }}>Select Freelancer</label>
              <select
                value={sf || ''}
                onChange={e => setSf(e.target.value ? Number(e.target.value) : null)}
                style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #e2e8f0', background: '#fff' }}
              >
                <option value="">All Freelancers</option>
                {fls.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
              </select>
            </div>
          )}
          {af === 'status' && (
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', marginBottom: '8px', display: 'block' }}>Payment Status</label>
              <select
                value={st}
                onChange={e => setSt(e.target.value)}
                style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #e2e8f0', background: '#fff' }}
              >
                <option value="">All Statuses</option>
                <option value="PENDING">Pending</option>
                <option value="PAID">Paid</option>
              </select>
            </div>
          )}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={resetFilters} style={{ padding: '12px 24px', borderRadius: '10px', border: '1px solid #e2e8f0', background: '#fff', fontWeight: '600', cursor: 'pointer' }}>Reset</button>
            <button onClick={applyFilters} style={{ padding: '12px 24px', borderRadius: '10px', border: 'none', background: '#0f172a', color: '#fff', fontWeight: '600', cursor: 'pointer' }}>Apply Filters</button>
          </div>
        </div>
      </div>

      {/* Selected Action Bar */}
      {sel.length > 0 && (
        <div style={{
          background: '#0f172a',
          padding: '24px 32px',
          borderRadius: '20px',
          marginBottom: '32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          color: 'white',
          animation: 'slideIn 0.3s ease-out'
        }}>
          <div>
            <div style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '4px' }}>Drafting Payment for {sel.length} tasks</div>
            <div style={{ fontSize: '28px', fontWeight: '800' }}>TOTAL: <span style={{ color: '#38bdf8' }}>${ttlAmt.toFixed(2)}</span></div>
          </div>
          <button onClick={() => setShowRev(true)} style={{ padding: '16px 32px', borderRadius: '12px', border: 'none', background: '#38bdf8', color: '#0f172a', fontWeight: '700', cursor: 'pointer', fontSize: '16px' }}>
            Process Batch
          </button>
        </div>
      )}

      {/* Table Section */}
      <div style={{ background: '#fff', borderRadius: '24px', overflow: 'hidden', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', border: '1px solid #f1f5f9' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #f1f5f9' }}>
              <th style={{ padding: '20px 24px', width: '50px' }}></th>
              <th style={{ padding: '20px 24px', fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>Task Entity</th>
              <th style={{ padding: '20px 24px', fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>Freelancer</th>
              <th style={{ padding: '20px 24px', fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>Status</th>
              <th style={{ padding: '20px 24px', fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', textAlign: 'right' }}>Amount</th>
              <th style={{ padding: '20px 24px', fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>Created (UTC)</th>
            </tr>
          </thead>
          <tbody>
            {displayed.map(w => (
              <tr
                key={w.id}
                onClick={() => window.location.href = `/worklogs/${w.id}`}
                style={{
                  borderBottom: '1px solid #f1f5f9',
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                  background: sel.includes(w.id) ? '#f0f9ff' : '#fff'
                }}
              >
                <td style={{ padding: '20px 24px' }} onClick={e => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={sel.includes(w.id)}
                    disabled={w.st === 'PAID'}
                    onChange={() => toggleSel(w.id)}
                    style={{ width: '20px', height: '20px', borderRadius: '6px' }}
                  />
                </td>
                <td style={{ padding: '20px 24px' }}>
                  <div style={{ fontWeight: '600', color: '#0f172a' }}>{w.t_nm}</div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>ID: #{w.id}</div>
                </td>
                <td style={{ padding: '20px 24px', color: '#334155' }}>{w.f_nm}</td>
                <td style={{ padding: '20px 24px' }}>
                  <span style={{
                    padding: '6px 12px',
                    borderRadius: '9999px',
                    fontSize: '11px',
                    fontWeight: '700',
                    background: w.st === 'PAID' ? '#dcfce7' : '#fef9c3',
                    color: w.st === 'PAID' ? '#166534' : '#854d0e'
                  }}>
                    {w.st}
                  </span>
                </td>
                <td style={{ padding: '20px 24px', textAlign: 'right', fontWeight: '700', color: '#0f172a' }}>
                  ${(w.ttl || 0).toFixed(2)}
                </td>
                <td style={{ padding: '20px 24px', fontSize: '12px', color: '#64748b', fontFamily: 'monospace' }}>
                  {w.c_at}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Client-side Pagination Controls */}
        <div style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc' }}>
          <div style={{ fontSize: '14px', color: '#64748b' }}>
            Showing {displayed.length} of {allData.length} records
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
              style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff', cursor: page === 1 ? 'not-allowed' : 'pointer' }}
            >
              Previous
            </button>
            <div style={{ display: 'flex', alignItems: 'center', padding: '0 12px', fontWeight: '600' }}>Page {page}</div>
            <button
              disabled={page * pageSize >= allData.length}
              onClick={() => setPage(page + 1)}
              style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff', cursor: page * pageSize >= allData.length ? 'not-allowed' : 'pointer' }}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Review Modal */}
      {showRev && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.75)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div style={{ background: '#fff', borderRadius: '24px', width: '90%', maxWidth: '600px', maxHeight: '80vh', overflow: 'hidden', display: 'flex', flexDirection: 'column', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)' }}>
            <div style={{ padding: '32px', borderBottom: '1px solid #f1f5f9' }}>
              <h2 style={{ fontSize: '24px', fontWeight: '800', color: '#0f172a', margin: 0 }}>Review Settlements</h2>
            </div>
            <div style={{ padding: '32px', overflowY: 'auto', flex: 1 }}>
              <div style={{ marginBottom: '24px' }}>
                <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '8px' }}>Total Payout</div>
                <div style={{ fontSize: '36px', fontWeight: '800', color: '#0f172a' }}>${ttlAmt.toFixed(2)}</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {selWls.map(w => (
                  <div key={w.id} style={{ padding: '16px', borderRadius: '16px', border: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '14px' }}>{w.t_nm}</div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>{w.f_nm}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ fontWeight: '700' }}>${w.ttl.toFixed(2)}</div>
                      <button
                        onClick={() => toggleSel(w.id)}
                        style={{ border: 'none', background: '#fee2e2', color: '#ef4444', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', fontSize: '11px', fontWeight: '700' }}
                      >
                        Exclude
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ padding: '24px 32px', background: '#f8fafc', display: 'flex', gap: '16px' }}>
              <button onClick={() => setShowRev(false)} style={{ flex: 1, padding: '14px', borderRadius: '12px', border: '1px solid #e2e8f0', background: '#fff', fontWeight: '600', cursor: 'pointer' }}>Cancel</button>
              <button onClick={procPay} style={{ flex: 1, padding: '14px', borderRadius: '12px', border: 'none', background: '#0f172a', color: '#fff', fontWeight: '600', cursor: 'pointer' }}>Confirm & Send Payment</button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      `}</style>
    </div>
  )
}
