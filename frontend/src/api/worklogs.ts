import { OpenAPI } from "@/client/core/OpenAPI"
import { request } from "@/client/core/request"

export type RemittanceStatus =
  | "PENDING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"

export type WorkLogRemittanceFilter = "REMITTED" | "UNREMITTED"

export type WorkLogListItem = {
  id: string
  task_id: string
  task_title: string
  user_id: string
  user_email: string
  user_full_name: string | null
  amount_cents: number
  remittance_id: string | null
  remittance_status: RemittanceStatus | null
}

export type WorkLogsPublic = {
  data: WorkLogListItem[]
  count: number
}

export type TimeEntryPublic = {
  id: string
  work_log_id: string
  entry_date: string
  duration_minutes: number
  amount_cents: number
  description: string | null
}

export type WorkLogDetail = WorkLogListItem & {
  time_entries: TimeEntryPublic[]
}

export type PaymentBatchPreview = {
  work_logs: WorkLogListItem[]
  total_amount_cents: number
  period_start: string
  period_end: string
}

export type ConfirmPaymentRequest = {
  period_start: string
  period_end: string
  include_work_log_ids: string[]
  exclude_freelancer_ids?: string[] | null
}

export type RemittancePublic = {
  id: string
  user_id: string
  period_start: string
  period_end: string
  status: RemittanceStatus
  total_amount_cents: number
}

export const WorklogsService = {
  listWorklogs(params: {
    skip?: number
    limit?: number
    date_from?: string | null
    date_to?: string | null
    remittance_status?: WorkLogRemittanceFilter | null
  } = {}): ReturnType<typeof request<WorkLogsPublic>> {
    const query: Record<string, unknown> = {
      skip: params.skip ?? 0,
      limit: params.limit ?? 100,
    }
    if (params.date_from != null) query.date_from = params.date_from
    if (params.date_to != null) query.date_to = params.date_to
    if (params.remittance_status != null)
      query.remittance_status = params.remittance_status
    return request(OpenAPI, {
      method: "GET",
      url: "/api/v1/worklogs/",
      query,
      errors: { 422: "Validation Error" },
    })
  },

  getWorklog(workLogId: string): ReturnType<typeof request<WorkLogDetail>> {
    return request(OpenAPI, {
      method: "GET",
      url: "/api/v1/worklogs/{work_log_id}",
      path: { work_log_id: workLogId },
      errors: { 422: "Validation Error" },
    })
  },
}

export const PaymentsService = {
  getPreview(params: {
    date_from: string
    date_to: string
  }): ReturnType<typeof request<PaymentBatchPreview>> {
    return request(OpenAPI, {
      method: "GET",
      url: "/api/v1/payments/preview",
      query: {
        date_from: params.date_from,
        date_to: params.date_to,
      },
      errors: { 422: "Validation Error" },
    })
  },

  confirm(body: ConfirmPaymentRequest): ReturnType<
    typeof request<RemittancePublic[]>
  > {
    return request(OpenAPI, {
      method: "POST",
      url: "/api/v1/payments/confirm",
      body,
      mediaType: "application/json",
      errors: { 422: "Validation Error" },
    })
  },
}
