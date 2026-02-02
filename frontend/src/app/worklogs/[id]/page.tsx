'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import TimeEntryRow from '@/components/TimeEntryRow';
import { getWorklog } from '@/lib/api';
import { WorklogWithDetails } from '@/types';
import { formatCurrency, formatHours, formatDate, getStatusColor } from '@/lib/utils';

export default function WorklogDetailPage() {
    const params = useParams();
    const [worklog, setWorklog] = useState<WorklogWithDetails | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchWorklog() {
            try {
                const data = await getWorklog(params.id as string);
                setWorklog(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load worklog');
            } finally {
                setLoading(false);
            }
        }
        if (params.id) {
            fetchWorklog();
        }
    }, [params.id]);

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

    if (error || !worklog) {
        return (
            <div className="app-container">
                <Sidebar />
                <main className="main-content">
                    <Link href="/worklogs" className="back-link">
                        ← Back to Worklogs
                    </Link>
                    <div className="empty-state">
                        <div className="empty-state-icon">⚠️</div>
                        <h2 className="empty-state-title">Worklog Not Found</h2>
                        <p className="empty-state-text">{error || 'The requested worklog could not be found'}</p>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="app-container">
            <Sidebar />
            <main className="main-content">
                <Link href="/worklogs" className="back-link">
                    ← Back to Worklogs
                </Link>

                {/* Header */}
                <div className="card" style={{ marginBottom: '1.5rem' }}>
                    <div className="card-body">
                        <div className="detail-header">
                            <div className="detail-info">
                                <h1 className="detail-title">{worklog.task?.title || 'Untitled Task'}</h1>
                                <div className="detail-meta">
                                    <div className="detail-meta-item">
                                        <span>👤</span>
                                        <span>{worklog.freelancer?.name}</span>
                                    </div>
                                    <div className="detail-meta-item">
                                        <span>📧</span>
                                        <span>{worklog.freelancer?.email}</span>
                                    </div>
                                    <div className="detail-meta-item">
                                        <span>💵</span>
                                        <span>{formatCurrency(worklog.freelancer?.hourly_rate || 0)}/hr</span>
                                    </div>
                                    <div className="detail-meta-item">
                                        <span>📅</span>
                                        <span>{formatDate(worklog.created_at)}</span>
                                    </div>
                                    <span className={`status-badge ${getStatusColor(worklog.status)}`}>
                                        {worklog.status}
                                    </span>
                                </div>
                            </div>
                            <div className="detail-amount">
                                <div className="detail-amount-value">{formatCurrency(worklog.total_amount)}</div>
                                <div className="detail-amount-label">{formatHours(worklog.total_hours)} logged</div>
                            </div>
                        </div>

                        {worklog.description && (
                            <div style={{ marginTop: '1rem' }}>
                                <h3 style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                    Description
                                </h3>
                                <p style={{ color: 'var(--text-secondary)' }}>{worklog.description}</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Time Entries */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">
                            <span>⏱️</span>
                            <span>Time Entries</span>
                        </h2>
                        <span style={{ color: 'var(--text-muted)' }}>
                            {worklog.time_entries.length} entries
                        </span>
                    </div>
                    <div className="card-body">
                        {worklog.time_entries.length === 0 ? (
                            <div className="empty-state">
                                <div className="empty-state-icon">⏱️</div>
                                <h2 className="empty-state-title">No Time Entries</h2>
                                <p className="empty-state-text">No time has been logged for this worklog</p>
                            </div>
                        ) : (
                            <div className="time-entry-list">
                                {worklog.time_entries.map((entry) => (
                                    <TimeEntryRow key={entry.id} entry={entry} />
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
