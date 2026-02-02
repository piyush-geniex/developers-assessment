'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import WorklogCard from '@/components/WorklogCard';
import DateRangeFilter from '@/components/DateRangeFilter';
import PaymentPreview from '@/components/PaymentPreview';
import FreelancerExclusion from '@/components/FreelancerExclusion';
import ConfirmModal from '@/components/ConfirmModal';
import { getEligibleWorklogs, getFreelancers, previewPaymentBatch, processPaymentBatch } from '@/lib/api';
import { Worklog, Freelancer } from '@/types';
import { getDateDaysAgo, getTodayDate, formatCurrency } from '@/lib/utils';

export default function PaymentsPage() {
    const router = useRouter();

    // Data
    const [worklogs, setWorklogs] = useState<Worklog[]>([]);
    const [freelancers, setFreelancers] = useState<Freelancer[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Date range
    const [dateFrom, setDateFrom] = useState(getDateDaysAgo(30));
    const [dateTo, setDateTo] = useState(getTodayDate());

    // Exclusions
    const [excludedWorklogIds, setExcludedWorklogIds] = useState<string[]>([]);
    const [excludedFreelancerIds, setExcludedFreelancerIds] = useState<string[]>([]);

    // Modal
    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [processing, setProcessing] = useState(false);

    // Load freelancers on mount
    useEffect(() => {
        getFreelancers().then(setFreelancers).catch(console.error);
    }, []);

    // Fetch eligible worklogs
    const fetchWorklogs = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getEligibleWorklogs(dateFrom, dateTo);
            setWorklogs(data);
            // Reset exclusions when fetching new data
            setExcludedWorklogIds([]);
            setExcludedFreelancerIds([]);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load worklogs');
        } finally {
            setLoading(false);
        }
    }, [dateFrom, dateTo]);

    // Filter out excluded worklogs
    const filteredWorklogs = worklogs.filter(
        (w) =>
            !excludedWorklogIds.includes(w.id) &&
            !excludedFreelancerIds.includes(w.freelancer_id)
    );

    // Calculate totals
    const totalAmount = filteredWorklogs.reduce((sum, w) => sum + w.total_amount, 0);
    const uniqueFreelancerIds = new Set(filteredWorklogs.map((w) => w.freelancer_id));
    const freelancersInBatch = freelancers.filter((f) =>
        worklogs.some((w) => w.freelancer_id === f.id)
    );

    // Toggle worklog exclusion
    const toggleWorklogExclusion = (id: string) => {
        setExcludedWorklogIds((prev) =>
            prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
        );
    };

    // Toggle freelancer exclusion
    const toggleFreelancerExclusion = (id: string) => {
        setExcludedFreelancerIds((prev) =>
            prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
        );
    };

    // Process payment
    const handleProcessPayment = async () => {
        setProcessing(true);
        try {
            await processPaymentBatch({
                date_from: dateFrom,
                date_to: dateTo,
                excluded_worklog_ids: excludedWorklogIds,
                excluded_freelancer_ids: excludedFreelancerIds,
            });
            setShowConfirmModal(false);
            router.push('/payments/history');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to process payment');
        } finally {
            setProcessing(false);
        }
    };

    return (
        <div className="app-container">
            <Sidebar />
            <main className="main-content">
                <div className="page-header">
                    <div>
                        <h1 className="page-title">
                            <div className="page-title-icon">💳</div>
                            Process Payments
                        </h1>
                        <p className="page-subtitle">Review and process freelancer payments</p>
                    </div>
                </div>

                {/* Date Range Filter */}
                <DateRangeFilter
                    dateFrom={dateFrom}
                    dateTo={dateTo}
                    onDateFromChange={setDateFrom}
                    onDateToChange={setDateTo}
                    onApply={fetchWorklogs}
                />

                {error && (
                    <div className="card" style={{ marginBottom: '1.5rem', borderColor: 'var(--accent-danger)' }}>
                        <div className="card-body" style={{ color: 'var(--accent-danger)' }}>
                            ⚠️ {error}
                        </div>
                    </div>
                )}

                {loading ? (
                    <div className="loading-spinner">
                        <div className="spinner"></div>
                    </div>
                ) : worklogs.length > 0 ? (
                    <>
                        {/* Payment Preview Summary */}
                        <PaymentPreview
                            totalAmount={totalAmount}
                            worklogsCount={filteredWorklogs.length}
                            freelancersCount={uniqueFreelancerIds.size}
                            dateFrom={dateFrom}
                            dateTo={dateTo}
                        />

                        {/* Freelancer Exclusion */}
                        <FreelancerExclusion
                            freelancers={freelancersInBatch}
                            excludedIds={excludedFreelancerIds}
                            onToggle={toggleFreelancerExclusion}
                        />

                        {/* Worklogs Selection */}
                        <div className="card">
                            <div className="card-header">
                                <h2 className="card-title">
                                    <span>📋</span>
                                    <span>Eligible Worklogs</span>
                                </h2>
                                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                    <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                                        {excludedWorklogIds.length} excluded
                                    </span>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                                        {filteredWorklogs.length} of {worklogs.length} selected
                                    </span>
                                </div>
                            </div>
                            <div className="card-body">
                                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem', fontSize: '0.875rem' }}>
                                    Click on a worklog card to exclude it from the payment batch
                                </p>
                                <div className="worklog-grid">
                                    {worklogs.map((worklog) => (
                                        <WorklogCard
                                            key={worklog.id}
                                            worklog={worklog}
                                            selectable
                                            selected={
                                                !excludedWorklogIds.includes(worklog.id) &&
                                                !excludedFreelancerIds.includes(worklog.freelancer_id)
                                            }
                                            onSelect={toggleWorklogExclusion}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                            <button
                                className="btn btn-secondary"
                                onClick={() => {
                                    setExcludedWorklogIds([]);
                                    setExcludedFreelancerIds([]);
                                }}
                                disabled={excludedWorklogIds.length === 0 && excludedFreelancerIds.length === 0}
                            >
                                Clear Exclusions
                            </button>
                            <button
                                className="btn btn-success"
                                onClick={() => setShowConfirmModal(true)}
                                disabled={filteredWorklogs.length === 0}
                            >
                                💳 Process Payment ({formatCurrency(totalAmount)})
                            </button>
                        </div>
                    </>
                ) : (
                    <div className="empty-state">
                        <div className="empty-state-icon">📋</div>
                        <h2 className="empty-state-title">No Eligible Worklogs</h2>
                        <p className="empty-state-text">
                            Select a date range and click "Apply Filter" to view eligible worklogs
                        </p>
                    </div>
                )}

                {/* Confirmation Modal */}
                <ConfirmModal
                    isOpen={showConfirmModal}
                    title="Confirm Payment Processing"
                    message={`You are about to process ${filteredWorklogs.length} worklogs for a total of ${formatCurrency(totalAmount)} to ${uniqueFreelancerIds.size} freelancer(s). This action cannot be undone.`}
                    confirmLabel="Process Payment"
                    cancelLabel="Cancel"
                    onConfirm={handleProcessPayment}
                    onCancel={() => setShowConfirmModal(false)}
                    isLoading={processing}
                />
            </main>
        </div>
    );
}
