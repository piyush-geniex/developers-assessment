
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { WorkLogService, type WorkLogsReadData } from "../client/WorkLogService"

export const useWorkLogs = (data: WorkLogsReadData = {}) => {
    return useQuery({
        queryKey: ["worklogs", data],
        queryFn: () => WorkLogService.readWorkLogs(data),
    })
}

export const useWorkLog = (id: string) => {
    return useQuery({
        queryKey: ["worklog", id],
        queryFn: () => WorkLogService.readWorkLog(id),
        enabled: !!id,
    })
}

export const usePayWorkLogs = () => {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (ids: string[]) => WorkLogService.payWorkLogs(ids),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["worklogs"] })
        },
    })
}
