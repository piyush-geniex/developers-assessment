'use client';

import { formatCurrency } from '@/lib/utils';

interface PaymentPreviewProps {
    totalAmount: number;
    worklogsCount: number;
    freelancersCount: number;
    dateFrom: string;
    dateTo: string;
}

export default function PaymentPreview({
    totalAmount,
    worklogsCount,
    freelancersCount,
    dateFrom,
    dateTo,
}: PaymentPreviewProps) {
    return (
        <div className="payment-summary">
            <div className="payment-summary-item">
                <div className="payment-summary-value">{formatCurrency(totalAmount)}</div>
                <div className="payment-summary-label">Total Amount</div>
            </div>
            <div className="payment-summary-item">
                <div className="payment-summary-value">{worklogsCount}</div>
                <div className="payment-summary-label">Worklogs</div>
            </div>
            <div className="payment-summary-item">
                <div className="payment-summary-value">{freelancersCount}</div>
                <div className="payment-summary-label">Freelancers</div>
            </div>
            <div className="payment-summary-item">
                <div className="payment-summary-value">
                    {dateFrom} → {dateTo}
                </div>
                <div className="payment-summary-label">Period</div>
            </div>
        </div>
    );
}
