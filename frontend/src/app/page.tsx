'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { getWorklogs, getPaymentBatches } from '@/lib/api';
import { Worklog, PaymentBatch } from '@/types';
import { formatCurrency, formatHours, formatDate } from '@/lib/utils';
import Link from 'next/link';

export default function DashboardPage() {
    const [worklogs, setWorklogs] = useState<Worklog[]>([]);
    const [batches, setBatches] = useState<PaymentBatch[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchData() {
            try {
                const [worklogsData, batchesData] = await Promise.all([
                    getWorklogs(),
                    getPaymentBatches(),
                ]);
                setWorklogs(worklogsData);
                setBatches(batchesData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load data');
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    // Calculate stats
    const pendingWorklogs = worklogs.filter((w) => w.status === 'pending');
    const totalPendingAmount = pendingWorklogs.reduce((sum, w) => sum + w.total_amount, 0);
    const totalPendingHours = pendingWorklogs.reduce((sum, w) => sum + w.total_hours, 0);
    const totalPaidAmount = batches.reduce((sum, b) => sum + b.total_amount, 0);
    const uniqueFreelancers = new Set(worklogs.map((w) => w.freelancer_id)).size;

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

    if (error) {
        return (
            <div className="app-container">
                <Sidebar />
                <main className="main-content">
                    <div className="empty-state">
                        <div className="empty-state-icon">⚠️</div>
                        <h2 className="empty-state-title">Error Loading Data</h2>
                        <p className="empty-state-text">{error}</p>
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
                            <div className="page-title-icon">📊</div>
                            Dashboard
                        </h1>
                        <p className="page-subtitle">Overview of worklogs and payments</p>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-card-icon">📋</div>
                        <div className="stat-card-value">{pendingWorklogs.length}</div>
                        <div className="stat-card-label">Pending Worklogs</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-card-icon">💰</div>
                        <div className="stat-card-value">{formatCurrency(totalPendingAmount)}</div>
                        <div className="stat-card-label">Pending Payments</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-card-icon">⏱️</div>
                        <div className="stat-card-value">{formatHours(totalPendingHours)}</div>
                        <div className="stat-card-label">Pending Hours</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-card-icon">👥</div>
                        <div className="stat-card-value">{uniqueFreelancers}</div>
                        <div className="stat-card-label">Active Freelancers</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-card-icon">✅</div>
                        <div className="stat-card-value">{formatCurrency(totalPaidAmount)}</div>
                        <div className="stat-card-label">Total Paid</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-card-icon">📦</div>
                        <div className="stat-card-value">{batches.length}</div>
                        <div className="stat-card-label">Payment Batches</div>
                    </div>
                </div>

                {/* Recent Worklogs */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">
                            <span>📋</span>
                            Recent Worklogs
                        </h2>
                        <Link href="/worklogs" className="btn btn-secondary" style={{ padding: '0.5rem 1rem' }}>
                            View All
                        </Link>
                    </div>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Task</th>
                                <th>Freelancer</th>
                                <th>Hours</th>
                                <th>Amount</th>
                                <th>Status</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {worklogs.slice(0, 5).map((worklog) => (
                                <tr key={worklog.id}>
                                    <td>
                                        <Link href={`/worklogs/${worklog.id}`} style={{ fontWeight: 500 }}>
                                            {worklog.task_title || 'Untitled'}
                                        </Link>
                                    </td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{worklog.freelancer_name}</td>
                                    <td>{formatHours(worklog.total_hours)}</td>
                                    <td style={{ fontWeight: 600, color: 'var(--accent-secondary)' }}>
                                        {formatCurrency(worklog.total_amount)}
                                    </td>
                                    <td>
                                        <span className={`status-badge status-${worklog.status}`}>
                                            {worklog.status}
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--text-muted)' }}>{formatDate(worklog.created_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Quick Actions */}
                <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                    <Link href="/payments" className="btn btn-primary">
                        💳 Process Payments
                    </Link>
                    <Link href="/worklogs" className="btn btn-secondary">
                        📋 View All Worklogs
                    </Link>
                </div>
            </main>
        </div>
    );
}
