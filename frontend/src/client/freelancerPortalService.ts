/**
 * Freelancer Portal API Service
 *
 * Uses a separate token (freelancer_token) from the admin portal (access_token)
 * to ensure complete authentication isolation.
 */

import { CancelablePromise, OpenAPI } from "./index"
import { request } from "./core/request"

// ============================================================================
// TYPES
// ============================================================================

export interface FreelancerToken {
  access_token: string
  token_type: string
}

export interface FreelancerRegister {
  name: string
  email: string
  password: string
  hourly_rate?: string
}

export interface FreelancerPublicMe {
  id: string
  name: string
  email: string
  hourly_rate: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface FreelancerUpdateMe {
  name?: string
  hourly_rate?: string
}

export interface FreelancerUpdatePassword {
  current_password: string
  new_password: string
}

export interface FreelancerDashboardStats {
  total_worklogs: number
  pending_worklogs: number
  approved_worklogs: number
  paid_worklogs: number
  rejected_worklogs: number
  total_hours_logged: string
  total_earned: string
  pending_amount: string
}

export interface FreelancerTimeEntryCreate {
  start_time: string
  end_time: string
  notes?: string | null
}

export interface FreelancerWorkLogCreate {
  task_description: string
  time_entries: FreelancerTimeEntryCreate[]
}

export interface FreelancerWorkLogUpdate {
  task_description?: string
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

export interface TimeEntryUpdate {
  start_time?: string
  end_time?: string
  notes?: string | null
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

export interface FreelancerPaymentInfo {
  batch_id: string
  processed_at: string
  total_amount: string
  worklog_count: number
  notes: string | null
  status: string
}

export interface Message {
  message: string
}

// ============================================================================
// TOKEN MANAGEMENT
// ============================================================================

const FREELANCER_TOKEN_KEY = "freelancer_token"

export function getFreelancerToken(): string | null {
  return localStorage.getItem(FREELANCER_TOKEN_KEY)
}

export function setFreelancerToken(token: string): void {
  localStorage.setItem(FREELANCER_TOKEN_KEY, token)
}

export function removeFreelancerToken(): void {
  localStorage.removeItem(FREELANCER_TOKEN_KEY)
}

export function isFreelancerLoggedIn(): boolean {
  return getFreelancerToken() !== null
}

// ============================================================================
// CUSTOM REQUEST WRAPPER (uses freelancer_token)
// ============================================================================

function freelancerRequest<T>(options: {
  method: "GET" | "POST" | "PATCH" | "DELETE"
  url: string
  body?: unknown
  formData?: Record<string, string>
}): CancelablePromise<T> {
  const token = getFreelancerToken()

  const headers: Record<string, string> = {}
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  if (options.formData) {
    // For OAuth2 login form
    return request(OpenAPI, {
      method: options.method,
      url: options.url,
      formData: options.formData,
      mediaType: "application/x-www-form-urlencoded",
    })
  }

  return request(OpenAPI, {
    method: options.method,
    url: options.url,
    body: options.body,
    headers,
  })
}

// ============================================================================
// AUTH SERVICE
// ============================================================================

export class FreelancerAuthService {
  /**
   * Login and get JWT token
   */
  static login(data: {
    username: string
    password: string
  }): CancelablePromise<FreelancerToken> {
    return freelancerRequest({
      method: "POST",
      url: "/api/v1/freelancer/login",
      formData: {
        username: data.username,
        password: data.password,
      },
    })
  }

  /**
   * Register new freelancer account
   */
  static register(data: FreelancerRegister): CancelablePromise<FreelancerPublicMe> {
    return freelancerRequest({
      method: "POST",
      url: "/api/v1/freelancer/register",
      body: data,
    })
  }

  /**
   * Get current freelancer profile
   */
  static getMe(): CancelablePromise<FreelancerPublicMe> {
    return freelancerRequest({
      method: "GET",
      url: "/api/v1/freelancer/me",
    })
  }

  /**
   * Update current freelancer profile
   */
  static updateMe(data: FreelancerUpdateMe): CancelablePromise<FreelancerPublicMe> {
    return freelancerRequest({
      method: "PATCH",
      url: "/api/v1/freelancer/me",
      body: data,
    })
  }

  /**
   * Update password
   */
  static updatePassword(data: FreelancerUpdatePassword): CancelablePromise<Message> {
    return freelancerRequest({
      method: "POST",
      url: "/api/v1/freelancer/me/password",
      body: data,
    })
  }
}

// ============================================================================
// PORTAL SERVICE
// ============================================================================

export class FreelancerPortalService {
  /**
   * Get dashboard statistics
   */
  static getDashboardStats(): CancelablePromise<FreelancerDashboardStats> {
    return freelancerRequest({
      method: "GET",
      url: "/api/v1/freelancer/dashboard/stats",
    })
  }

  /**
   * Get my worklogs
   */
  static getMyWorklogs(params?: {
    skip?: number
    limit?: number
    status?: WorkLogStatus[]
  }): CancelablePromise<WorkLogsSummaryPublic> {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append("skip", params.skip.toString())
    if (params?.limit) queryParams.append("limit", params.limit.toString())
    if (params?.status) {
      params.status.forEach((s) => queryParams.append("status", s))
    }

    const url = `/api/v1/freelancer/worklogs${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
    return freelancerRequest({
      method: "GET",
      url,
    })
  }

  /**
   * Get worklog detail
   */
  static getWorklogDetail(worklogId: string): CancelablePromise<WorkLogDetail> {
    return freelancerRequest({
      method: "GET",
      url: `/api/v1/freelancer/worklogs/${worklogId}`,
    })
  }

  /**
   * Create new worklog
   */
  static createWorklog(data: FreelancerWorkLogCreate): CancelablePromise<WorkLogDetail> {
    return freelancerRequest({
      method: "POST",
      url: "/api/v1/freelancer/worklogs",
      body: data,
    })
  }

  /**
   * Update worklog (only if PENDING)
   */
  static updateWorklog(
    worklogId: string,
    data: FreelancerWorkLogUpdate
  ): CancelablePromise<WorkLogDetail> {
    return freelancerRequest({
      method: "PATCH",
      url: `/api/v1/freelancer/worklogs/${worklogId}`,
      body: data,
    })
  }

  /**
   * Delete worklog (only if PENDING)
   */
  static deleteWorklog(worklogId: string): CancelablePromise<Message> {
    return freelancerRequest({
      method: "DELETE",
      url: `/api/v1/freelancer/worklogs/${worklogId}`,
    })
  }

  /**
   * Add time entry to worklog (only if PENDING)
   */
  static addTimeEntry(
    worklogId: string,
    data: FreelancerTimeEntryCreate
  ): CancelablePromise<TimeEntryPublic> {
    return freelancerRequest({
      method: "POST",
      url: `/api/v1/freelancer/worklogs/${worklogId}/time-entries`,
      body: data,
    })
  }

  /**
   * Update time entry (only if parent worklog is PENDING)
   */
  static updateTimeEntry(
    entryId: string,
    data: TimeEntryUpdate
  ): CancelablePromise<TimeEntryPublic> {
    return freelancerRequest({
      method: "PATCH",
      url: `/api/v1/freelancer/time-entries/${entryId}`,
      body: data,
    })
  }

  /**
   * Delete time entry (only if parent worklog is PENDING)
   */
  static deleteTimeEntry(entryId: string): CancelablePromise<Message> {
    return freelancerRequest({
      method: "DELETE",
      url: `/api/v1/freelancer/time-entries/${entryId}`,
    })
  }

  /**
   * Get payment history
   */
  static getMyPayments(): CancelablePromise<FreelancerPaymentInfo[]> {
    return freelancerRequest({
      method: "GET",
      url: "/api/v1/freelancer/payments",
    })
  }
}
