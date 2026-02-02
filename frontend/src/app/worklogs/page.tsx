'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import WorklogCard from '@/components/WorklogCard';
import { getWorklogs, getFreelancers } from '@/lib/api';
import { Worklog, Freelancer } from '@/types';

export default function WorklogsPage() {
    const [worklogs, setWorklogs] = useState<Worklog[]>([]);
    const [freelancers, setFreelancers] = useState<Freelancer[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filters
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [freelancerFilter, setFreelancerFilter] = useState<string>('');

    useEffect(() => {
        async function fetchData() {
            try {
                const [worklogsData, freelancersData] = await Promise.all([
                    getWorklogs(),
                    getFreelancers(),
                ]);
                setWorklogs(worklogsData);
                setFreelancers(freelancersData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load worklogs');
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    // Apply filters
    let filteredWorklogs = worklogs;
    if (statusFilter) {
        filteredWorklogs = filteredWorklogs.filter((w) => w.status === statusFilter);
    }
    if (freelancerFilter) {
        filteredWorklogs = filteredWorklogs.filter((w) => w.freelancer_id === freelancerFilter);
    }

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
                        <h2 className="empty-state-title">Error Loading Worklogs</h2>
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
                            <div className="page-title-icon">📋</div>
                            Worklogs
                        </h1>
                        <p className="page-subtitle">View and manage all freelancer worklogs</p>
                    </div>
                </div>

                {/* Filters */}
                <div className="filters-section">
                    <div className="filters-row">
                        <div className="form-group">
                            <label className="form-label">Filter by Status</label>
                            <select
                                className="form-select"
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                            >
                                <option value="">All Statuses</option>
                                <option value="pending">Pending</option>
                                <option value="paid">Paid</option>
                                <option value="cancelled">Cancelled</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label className="form-label">Filter by Freelancer</label>
                            <select
                                className="form-select"
                                value={freelancerFilter}
                                onChange={(e) => setFreelancerFilter(e.target.value)}
                            >
                                <option value="">All Freelancers</option>
                                {freelancers.map((f) => (
                                    <option key={f.id} value={f.id}>
                                        {f.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <button
                            className="btn btn-secondary"
                            onClick={() => {
                                setStatusFilter('');
                                setFreelancerFilter('');
                            }}
                        >
                            Clear Filters
                        </button>
                    </div>
                </div>

                {/* Results count */}
                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    Showing {filteredWorklogs.length} of {worklogs.length} worklogs
                </p>

                {/* Worklog Grid */}
                {filteredWorklogs.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">📋</div>
                        <h2 className="empty-state-title">No Worklogs Found</h2>
                        <p className="empty-state-text">Try adjusting your filters</p>
                    </div>
                ) : (
                    <div className="worklog-grid">
                        {filteredWorklogs.map((worklog) => (
                            <WorklogCard key={worklog.id} worklog={worklog} />
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
