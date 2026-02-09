import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'

export const Route = createFileRoute('/_layout/worklogs/$id')({
    component: WorklogDetailPage,
})

function WorklogDetailPage() {
    const axios = require('axios').default
    axios.defaults.baseURL = 'http://localhost:8000'

    const { id } = Route.useParams()
    const [wl, setWl] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(() => {
        loadData()
    }, [id])

    const loadData = async () => {
        try {
            setLoading(true)
            const res = await axios.get(`http://localhost:8000/api/v1/worklog/worklogs/${id}`)
            setWl(res.data)
            setLoading(false)
        } catch (err) {
            setError('Failed to load worklog. Please check your connection or ensure the ID is correct.')
            console.error(err)
            setLoading(false)
        }
    }

    if (loading) return (
        <div style={{ padding: '100px', textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: '600', color: '#667eea', animation: 'pulse 2s infinite' }}>Fetching Record...</div>
        </div>
    )

    if (error || !wl) return (
        <div style={{ padding: '100px', textAlign: 'center' }}>
            <div style={{ color: '#e74c3c', fontSize: '18px' }}>{error || 'Record not found.'}</div>
            <a href="/worklogs" style={{ marginTop: '20px', display: 'inline-block', color: '#667eea', textDecoration: 'none' }}>Back to Dashboard</a>
        </div>
    )

    return (
        <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto', fontFamily: 'Inter, system-ui, sans-serif' }}>
            <div style={{ marginBottom: '32px' }}>
                <a href="/worklogs" style={{ color: '#64748b', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: '600' }}>
                    <span>←</span> Back to Settlement Hub
                </a>
            </div>

            <div style={{
                background: '#fff',
                borderRadius: '24px',
                padding: '40px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                border: '1px solid #f1f5f9',
                marginBottom: '32px'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
                    <div>
                        <div style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Task Identifier #{wl.id}</div>
                        <h1 style={{ margin: 0, fontSize: '32px', fontWeight: '800', color: '#0f172a' }}>{wl.t_nm}</h1>
                    </div>
                    <span style={{
                        padding: '8px 16px',
                        borderRadius: '9999px',
                        fontSize: '13px',
                        fontWeight: '700',
                        background: wl.st === 'PAID' ? '#dcfce7' : '#fef9c3',
                        color: wl.st === 'PAID' ? '#166534' : '#854d0e'
                    }}>
                        {wl.st}
                    </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '32px' }}>
                    <div>
                        <div style={{ fontSize: '12px', fontWeight: '600', color: '#64748b', marginBottom: '4px' }}>Freelancer</div>
                        <div style={{ fontWeight: '700', color: '#0f172a' }}>{wl.f_nm}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: '12px', fontWeight: '600', color: '#64748b', marginBottom: '4px' }}>Total Payout</div>
                        <div style={{ fontSize: '24px', fontWeight: '800', color: '#0f172a' }}>${(wl.ttl || 0).toFixed(2)}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: '12px', fontWeight: '600', color: '#64748b', marginBottom: '4px' }}>Logged At (UTC)</div>
                        <div style={{ fontSize: '14px', color: '#334155', fontFamily: 'monospace' }}>{wl.c_at}</div>
                    </div>
                </div>
            </div>

            <div style={{ background: '#fff', borderRadius: '24px', overflow: 'hidden', border: '1px solid #f1f5f9' }}>
                <div style={{ padding: '24px 32px', borderBottom: '1px solid #f1f5f9', background: '#f8fafc' }}>
                    <h2 style={{ margin: 0, fontSize: '18px', fontWeight: '800', color: '#0f172a' }}>Itemized Time Entries</h2>
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <th style={{ padding: '16px 32px', fontSize: '11px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>Description</th>
                            <th style={{ padding: '16px 32px', fontSize: '11px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', textAlign: 'center' }}>Hours</th>
                            <th style={{ padding: '16px 32px', fontSize: '11px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', textAlign: 'right' }}>Rate</th>
                            <th style={{ padding: '16px 32px', fontSize: '11px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', textAlign: 'right' }}>Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(wl.ents || []).map((e: any) => (
                            <tr key={e.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                <td style={{ padding: '16px 32px' }}>
                                    <div style={{ fontWeight: '600', color: '#0f172a', fontSize: '14px' }}>{e.desc}</div>
                                    <div style={{ fontSize: '12px', color: '#64748b' }}>{e.e_dt}</div>
                                </td>
                                <td style={{ padding: '16px 32px', textAlign: 'center', fontWeight: '700' }}>{e.h}h</td>
                                <td style={{ padding: '16px 32px', textAlign: 'right', color: '#64748b', fontSize: '14px' }}>${e.r.toFixed(2)}</td>
                                <td style={{ padding: '16px 32px', textAlign: 'right', fontWeight: '700', color: '#0f172a' }}>${e.amt.toFixed(2)}</td>
                            </tr>
                        ))}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colSpan={3} style={{ padding: '24px 32px', textAlign: 'right', fontWeight: '700', color: '#64748b' }}>Total Settlement</td>
                            <td style={{ padding: '24px 32px', textAlign: 'right', fontSize: '20px', fontWeight: '800', color: '#0f172a' }}>${wl.ttl.toFixed(2)}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

            <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      `}</style>
        </div>
    )
}
