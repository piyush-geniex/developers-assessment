
import type { CancelablePromise } from './core/CancelablePromise';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

export type WorkLogPublic = {
    id: string;
    freelancer_id: string;
    task_name: string;
    status: string;
    created_at: string;
    total_duration_hours: number;
    total_amount: number;
};

export type WorkLogsPublic = {
    data: Array<WorkLogPublic>;
    count: number;
};

export type TimeEntryPublic = {
    id: string;
    worklog_id: string;
    start_time: string;
    end_time: string;
    description: string;
    rate: number;
};

export type WorkLogDetail = WorkLogPublic & {
    time_entries?: Array<TimeEntryPublic>; // Depending on how we implemented the backend
};

export type WorkLogsReadData = {
    skip?: number;
    limit?: number;
    date_from?: string;
    date_to?: string;
    freelancer_id?: string;
};

export class WorkLogService {
    public static readWorkLogs(data: WorkLogsReadData = {}): CancelablePromise<WorkLogsPublic> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/worklogs/',
            query: {
                skip: data.skip,
                limit: data.limit,
                date_from: data.date_from,
                date_to: data.date_to,
                freelancer_id: data.freelancer_id
            },
            errors: {
                422: 'Validation Error'
            }
        });
    }

    public static readWorkLog(id: string): CancelablePromise<WorkLogDetail> {
        return __request(OpenAPI, {
            method: 'GET',
            url: `/api/v1/worklogs/${id}`,
            errors: {
                422: 'Validation Error',
                404: 'Not Found'
            }
        });
    }

    public static payWorkLogs(ids: string[]): CancelablePromise<WorkLogPublic[]> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/worklogs/pay',
            body: ids, // sending array directly as request body
            mediaType: 'application/json',
            errors: {
                422: 'Validation Error'
            }
        });
    }
}
