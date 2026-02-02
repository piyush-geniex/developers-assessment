/**
 * API Client for WorkLog Payment Dashboard
 */

import {
    Worklog,
    WorklogWithDetails,
    Freelancer,
    PaymentBatch,
    PaymentBatchWithPayments,
    PaymentPreviewRequest,
    PaymentPreviewResponse,
    PaymentProcessRequest,
    PaymentProcessResponse,
    WorklogFilters,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(
    endpoint: string,
    options?: RequestInit
): Promise<T> {
    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
}

// ==================== Worklog API ====================

export async function getWorklogs(filters?: WorklogFilters): Promise<Worklog[]> {
    const params = new URLSearchParams();

    if (filters?.date_from) params.append('date_from', filters.date_from);
    if (filters?.date_to) params.append('date_to', filters.date_to);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.freelancer_id) params.append('freelancer_id', filters.freelancer_id);

    const query = params.toString();
    return fetchApi<Worklog[]>(`/api/worklogs${query ? `?${query}` : ''}`);
}

export async function getWorklog(id: string): Promise<WorklogWithDetails> {
    return fetchApi<WorklogWithDetails>(`/api/worklogs/${id}`);
}

export async function getEligibleWorklogs(
    date_from: string,
    date_to: string
): Promise<Worklog[]> {
    return fetchApi<Worklog[]>(
        `/api/worklogs/eligible?date_from=${date_from}&date_to=${date_to}`
    );
}

// ==================== Freelancer API ====================

export async function getFreelancers(): Promise<Freelancer[]> {
    return fetchApi<Freelancer[]>('/api/freelancers');
}

export async function getFreelancer(id: string): Promise<Freelancer> {
    return fetchApi<Freelancer>(`/api/freelancers/${id}`);
}

// ==================== Payment API ====================

export async function previewPaymentBatch(
    request: PaymentPreviewRequest
): Promise<PaymentPreviewResponse> {
    return fetchApi<PaymentPreviewResponse>('/api/payments/preview', {
        method: 'POST',
        body: JSON.stringify(request),
    });
}

export async function processPaymentBatch(
    request: PaymentProcessRequest
): Promise<PaymentProcessResponse> {
    return fetchApi<PaymentProcessResponse>('/api/payments/process', {
        method: 'POST',
        body: JSON.stringify(request),
    });
}

export async function getPaymentBatches(): Promise<PaymentBatch[]> {
    return fetchApi<PaymentBatch[]>('/api/payments/batches');
}

export async function getPaymentBatch(id: string): Promise<PaymentBatchWithPayments> {
    return fetchApi<PaymentBatchWithPayments>(`/api/payments/batches/${id}`);
}
