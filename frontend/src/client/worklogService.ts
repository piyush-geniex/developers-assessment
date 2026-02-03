// WorkLog API Service
import type { CancelablePromise } from "./core/CancelablePromise"
import { OpenAPI } from "./core/OpenAPI"
import { request as __request } from "./core/request"

// Types
export type WorkLogStatus = "pending" | "approved" | "paid" | "rejected"

export interface WorkLogSummary {
  id: string
  task_description: string
  freelancer_id: string
  freelancer_name: string
  freelancer_email: string
  hourly_rate: string
  status: WorkLogStatus
  created_at: string
  total_duration_minutes: number
  total_amount: string
  time_entry_count: number
}

export interface WorkLogsSummaryPublic {
  data: WorkLogSummary[]
  count: number
}

export interface TimeEntryPublic {
  id: string
  work_log_id: string
  start_time: string
  end_time: string
  notes: string | null
  duration_minutes: number
  created_at: string
}

export interface FreelancerPublic {
  id: string
  name: string
  email: string
  hourly_rate: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WorkLogDetail {
  id: string
  task_description: string
  freelancer_id: string
  status: WorkLogStatus
  payment_batch_id: string | null
  created_at: string
  updated_at: string
  freelancer: FreelancerPublic
  time_entries: TimeEntryPublic[]
  total_duration_minutes: number
  total_amount: string
}

export interface FreelancerPaymentSummary {
  freelancer_id: string
  freelancer_name: string
  freelancer_email: string
  hourly_rate: string
  worklog_count: number
  total_duration_minutes: number
  total_amount: string
  worklogs: WorkLogSummary[]
}

export interface PaymentIssue {
  worklog_id: string
  issue_type: string
  message: string
}

export interface PaymentPreviewResponse {
  total_worklogs: number
  total_amount: string
  freelancer_breakdown: FreelancerPaymentSummary[]
  issues: PaymentIssue[]
  can_process: boolean
}

export interface PaymentProcessResponse {
  batch_id: string
  total_worklogs: number
  total_amount: string
  status: string
}

export interface PaymentBatchPublic {
  id: string
  processed_at: string
  processed_by_id: string
  total_amount: string
  status: string
  notes: string | null
  worklog_count: number
}

export interface PaymentBatchesPublic {
  data: PaymentBatchPublic[]
  count: number
}

export interface FreelancersPublic {
  data: FreelancerPublic[]
  count: number
}

// WorkLog Service
export class WorkLogsService {
  /**
   * Get aggregated worklog summary
   */
  public static getWorklogsSummary(data: {
    skip?: number
    limit?: number
    freelancerId?: string
    status?: WorkLogStatus[]
    dateFrom?: string
    dateTo?: string
  } = {}): CancelablePromise<WorkLogsSummaryPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/worklogs/summary",
      query: {
        skip: data.skip,
        limit: data.limit,
        freelancer_id: data.freelancerId,
        status: data.status,
        date_from: data.dateFrom,
        date_to: data.dateTo,
      },
      errors: {
        422: "Validation Error",
      },
    })
  }

  /**
   * Get worklog detail with time entries
   */
  public static getWorklogDetail(data: {
    worklogId: string
  }): CancelablePromise<WorkLogDetail> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/worklogs/{worklog_id}/detail",
      path: {
        worklog_id: data.worklogId,
      },
      errors: {
        422: "Validation Error",
      },
    })
  }

  /**
   * Update worklog status
   */
  public static updateWorklogStatus(data: {
    worklogId: string
    status: WorkLogStatus
  }): CancelablePromise<unknown> {
    return __request(OpenAPI, {
      method: "PATCH",
      url: "/api/v1/worklogs/{worklog_id}/status",
      path: {
        worklog_id: data.worklogId,
      },
      query: {
        status: data.status,
      },
      errors: {
        422: "Validation Error",
      },
    })
  }
}

// Payment Service
export class PaymentsService {
  /**
   * Preview payment for selected worklogs
   */
  public static previewPayment(data: {
    worklogIds: string[]
  }): CancelablePromise<PaymentPreviewResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/payments/preview",
      body: data.worklogIds,
      mediaType: "application/json",
      errors: {
        422: "Validation Error",
      },
    })
  }

  /**
   * Process payment for selected worklogs
   */
  public static processPayment(data: {
    worklogIds: string[]
    notes?: string
  }): CancelablePromise<PaymentProcessResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/payments/process",
      body: {
        worklog_ids: data.worklogIds,
        notes: data.notes,
      },
      mediaType: "application/json",
      errors: {
        422: "Validation Error",
      },
    })
  }

  /**
   * Get payment batch history
   */
  public static getPaymentBatches(data: {
    skip?: number
    limit?: number
  } = {}): CancelablePromise<PaymentBatchesPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/payments/batches",
      query: {
        skip: data.skip,
        limit: data.limit,
      },
      errors: {
        422: "Validation Error",
      },
    })
  }
}

// Freelancer Service
export class FreelancersService {
  /**
   * Get all freelancers
   */
  public static getFreelancers(data: {
    skip?: number
    limit?: number
    isActive?: boolean
  } = {}): CancelablePromise<FreelancersPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/freelancers/",
      query: {
        skip: data.skip,
        limit: data.limit,
        is_active: data.isActive,
      },
      errors: {
        422: "Validation Error",
      },
    })
  }
}
