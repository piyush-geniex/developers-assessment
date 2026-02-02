/**
 * TypeScript type definitions for the WorkLog Payment Dashboard
 */

// ==================== Freelancer Types ====================

export interface Freelancer {
    id: string;
    name: string;
    email: string;
    hourly_rate: number;
    created_at: string | null;
}

// ==================== Task Types ====================

export interface Task {
    id: string;
    title: string;
    description: string | null;
    status: string;
    created_at: string | null;
}

// ==================== TimeEntry Types ====================

export interface TimeEntry {
    id: string;
    worklog_id: string;
    start_time: string;
    end_time: string;
    hours: number;
    description: string | null;
    created_at: string | null;
}

// ==================== Worklog Types ====================

export interface Worklog {
    id: string;
    freelancer_id: string;
    task_id: string;
    description: string | null;
    total_hours: number;
    total_amount: number;
    status: string;
    created_at: string | null;
    freelancer_name?: string | null;
    freelancer_email?: string | null;
    freelancer_hourly_rate?: number | null;
    task_title?: string | null;
    time_entries_count?: number | null;
}

export interface WorklogWithDetails {
    id: string;
    freelancer_id: string;
    task_id: string;
    description: string | null;
    total_hours: number;
    total_amount: number;
    status: string;
    created_at: string | null;
    freelancer: Freelancer | null;
    task: Task | null;
    time_entries: TimeEntry[];
}

// ==================== Payment Types ====================

export interface Payment {
    id: string;
    batch_id: string | null;
    worklog_id: string;
    freelancer_id: string;
    amount: number;
    status: string;
    created_at: string | null;
    freelancer_name?: string | null;
    worklog_description?: string | null;
    task_title?: string | null;
}

export interface PaymentBatch {
    id: string;
    date_from: string;
    date_to: string;
    total_amount: number;
    status: string;
    created_at: string | null;
    processed_at: string | null;
    payments_count?: number | null;
}

export interface PaymentBatchWithPayments extends PaymentBatch {
    payments: Payment[];
}

// ==================== Request/Response Types ====================

export interface PaymentPreviewRequest {
    date_from: string;
    date_to: string;
    excluded_worklog_ids: string[];
    excluded_freelancer_ids: string[];
}

export interface PaymentPreviewResponse {
    date_from: string;
    date_to: string;
    worklogs: Worklog[];
    total_amount: number;
    total_worklogs: number;
    freelancers_count: number;
    excluded_worklog_ids: string[];
    excluded_freelancer_ids: string[];
}

export interface PaymentProcessRequest {
    date_from: string;
    date_to: string;
    excluded_worklog_ids: string[];
    excluded_freelancer_ids: string[];
}

export interface PaymentProcessResponse {
    batch: PaymentBatch;
    payments: Payment[];
    total_amount: number;
    worklogs_paid: number;
    freelancers_paid: number;
}

// ==================== Filter Types ====================

export interface WorklogFilters {
    date_from?: string;
    date_to?: string;
    status?: string;
    freelancer_id?: string;
}
