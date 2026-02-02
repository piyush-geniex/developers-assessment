'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import { getPaymentBatches, getPaymentBatch } from '@/lib/api';
import { PaymentBatch, PaymentBatchWithPayments } from '@/types';
import { formatCurrency, formatDate, getStatusColor } from '@/lib/utils';

export default function PaymentHistoryPage() {
    const [batches, setBatches] = useState<PaymentBatch[]>([]);
    const [selectedBatch, setSelectedBatch] = useState<PaymentBatchWithPayments | null>(null);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchBatches() {
            try {
                const data = await getPaymentBatches();
                setBatches(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load payment history');
            } finally {
                setLoading(false);
            }
        }
        fetchBatches();
    }, []);

    const handleViewBatch = async (batchId: string) => {
        setDetailLoading(true);
        try {
            const data = await getPaymentBatch(batchId);
            setSelectedBatch(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load batch details');
        } finally {
            setDetailLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="app-container">
                <Sidebar />
                <main className="main-content">
                    <div className="loading-spinner">
                        <div className="spinner"></div>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="app-container">
            <Sidebar />
            <main className="main-content">
                <div className="page-header">
                    <div>
                        <h1 className="page-title">
                            <div className="page-title-icon">📜</div>
                            Payment History
                        </h1>
                        <p className="page-subtitle">View past payment batches and details</p>
                    </div>
                    <Link href="/payments" className="btn btn-primary">
                        💳 New Payment
                    </Link>
                </div>

                {error && (
                    <div className="card" style={{ marginBottom: '1.5rem', borderColor: 'var(--accent-danger)' }}>
                        <div className="card-body" style={{ color: 'var(--accent-danger)' }}>
                            ⚠️ {error}
                        </div>
                    </div>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: selectedBatch ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
                    {/* Batches List */}
                    <div className="card">
                        <div className="card-header">
                            <h2 className="card-title">
                                <span>📦</span>
                                <span>Payment Batches</span>
                            </h2>
                            <span style={{ color: 'var(--text-muted)' }}>{batches.length} batches</span>
                        </div>
                        {batches.length === 0 ? (
                            <div className="card-body">
                                <div className="empty-state">
                                    <div className="empty-state-icon">📦</div>
                                    <h2 className="empty-state-title">No Payment History</h2>
                                    <p className="empty-state-text">Process your first payment batch to see history</p>
                                </div>
                            </div>
                        ) : (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Period</th>
                                        <th>Amount</th>
                                        <th>Payments</th>
                                        <th>Status</th>
                                        <th>Processed</th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {batches.map((batch) => (
                                        <tr key={batch.id}>
                                            <td>
                                                <div style={{ fontWeight: 500 }}>
                                                    {formatDate(batch.date_from)} - {formatDate(batch.date_to)}
                                                </div>
                                            </td>
                                            <td style={{ fontWeight: 600, color: 'var(--accent-success)' }}>
                                                {formatCurrency(batch.total_amount)}
                                            </td>
                                            <td>{batch.payments_count || 0}</td>
                                            <td>
                                                <span className={`status-badge ${getStatusColor(batch.status)}`}>
                                                    {batch.status}
                                                </span>
                                            </td>
                                            <td style={{ color: 'var(--text-muted)' }}>
                                                {formatDate(batch.processed_at)}
                                            </td>
                                            <td>
                                                <button
                                                    className="btn btn-secondary"
                                                    style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}
                                                    onClick={() => handleViewBatch(batch.id)}
                                                >
                                                    View
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>

                    {/* Batch Details */}
                    {selectedBatch && (
                        <div className="card">
                            <div className="card-header">
                                <h2 className="card-title">
                                    <span>📄</span>
                                    <span>Batch Details</span>
                                </h2>
                                <button
                                    className="modal-close"
                                    onClick={() => setSelectedBatch(null)}
                                    style={{ position: 'static' }}
                                >
                                    ✕
                                </button>
                            </div>
                            {detailLoading ? (
                                <div className="card-body">
                                    <div className="loading-spinner">
                                        <div className="spinner"></div>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <div className="card-body" style={{ borderBottom: '1px solid var(--border-primary)' }}>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                                            <div>
                                                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                                                    Period
                                                </div>
                                                <div style={{ fontWeight: 500 }}>
                                                    {formatDate(selectedBatch.date_from)} - {formatDate(selectedBatch.date_to)}
                                                </div>
                                            </div>
                                            <div>
                                                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                                                    Total Amount
                                                </div>
                                                <div style={{ fontWeight: 700, fontSize: '1.25rem', color: 'var(--accent-success)' }}>
                                                    {formatCurrency(selectedBatch.total_amount)}
                                                </div>
                                            </div>
                                            <div>
                                                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                                                    Status
                                                </div>
                                                <span className={`status-badge ${getStatusColor(selectedBatch.status)}`}>
                                                    {selectedBatch.status}
                                                </span>
                                            </div>
                                            <div>
                                                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                                                    Processed
                                                </div>
                                                <div>{formatDate(selectedBatch.processed_at)}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="card-body">
                                        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '1rem' }}>
                                            Individual Payments ({selectedBatch.payments.length})
                                        </h3>
                                        {selectedBatch.payments.length === 0 ? (
                                            <p style={{ color: 'var(--text-muted)' }}>No payment records</p>
                                        ) : (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                                {selectedBatch.payments.map((payment) => (
                                                    <div
                                                        key={payment.id}
                                                        style={{
                                                            display: 'flex',
                                                            justifyContent: 'space-between',
                                                            alignItems: 'center',
                                                            padding: '0.75rem',
                                                            background: 'var(--bg-secondary)',
                                                            borderRadius: 'var(--radius-md)',
                                                            border: '1px solid var(--border-primary)',
                                                        }}
                                                    >
                                                        <div>
                                                            <div style={{ fontWeight: 500 }}>{payment.freelancer_name}</div>
                                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                                {payment.task_title}
                                                            </div>
                                                        </div>
                                                        <div style={{ fontWeight: 600, color: 'var(--accent-secondary)' }}>
                                                            {formatCurrency(payment.amount)}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
