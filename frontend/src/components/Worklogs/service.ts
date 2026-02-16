import axios from "axios"

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"

export const WorklogsService = {
    readWorklogs: async (params?: { skip?: number; limit?: number; start_date?: string; end_date?: string }) => {
        const queryParams = new URLSearchParams()

        if (params?.skip !== undefined) queryParams.append("skip", params.skip.toString())
        if (params?.limit !== undefined) queryParams.append("limit", params.limit.toString())
        if (params?.start_date) queryParams.append("start_date", params.start_date)
        if (params?.end_date) queryParams.append("end_date", params.end_date)

        const url = `${apiUrl}/api/v1/worklogs/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
        const response = await axios.get(url)
        return response.data
    },

    readWorklog: async (id: number) => {
        const url = `${apiUrl}/api/v1/worklogs/${id}`
        const response = await axios.get(url)
        return response.data
    },

    createPaymentBatch: async (worklogIds: number[]) => {
        const url = `${apiUrl}/api/v1/worklogs/payment-batch`
        const response = await axios.post(url, { worklog_ids: worklogIds })
        return response.data
    },

    updateWorklog: async (id: number, data: { status?: string }) => {
        const url = `${apiUrl}/api/v1/worklogs/${id}`
        const response = await axios.put(url, data)
        return response.data
    },

    createWorklog: async (data: any) => {
        const url = `${apiUrl}/api/v1/worklogs/`
        const response = await axios.post(url, data)
        return response.data
    },
}
