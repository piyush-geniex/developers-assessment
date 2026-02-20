import { useQuery } from "@tanstack/react-query"
import { useState, useEffect } from "react"

import type { TaskItem, WorkLogEntryItem } from "@/client"
import { WorkLogsService } from "@/client"
import { Checkbox } from "@/components/ui/checkbox"
import { useTaskSelection } from "./TaskSelectionContext"

interface TaskWorkLogsSubComponentProps {
  task: TaskItem
}

// Helper function to extract timezone from ISO string
const extractTimezone = (isoString: string): string => {
  const timezoneMatch = isoString.match(/([+-]\d{2}:\d{2}|Z)$/)
  if (timezoneMatch) {
    const tz = timezoneMatch[1]
    if (tz === "Z") {
      return "UTC"
    }
    return `UTC${tz}`
  }
  return "UTC"
}

function formatAmount(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount)
}

export const TaskWorkLogsSubComponent = ({
  task,
}: TaskWorkLogsSubComponentProps) => {
  const { data: worklogsData, isLoading: worklogsLoading, error: worklogsError } = useQuery({
    queryKey: ["worklogs", task.id],
    queryFn: () => WorkLogsService.tasksReadWorkLogs({ taskId: task.id }),
  })

  const worklogs = (worklogsData?.data || []) as WorkLogEntryItem[]
  const [selected, setSelected] = useState<Record<string, boolean>>({})
  
  const { selectedTasks, toggleWorklog, toggleTask, selectAllMode, setSelectAllMode } = useTaskSelection()

  // Auto-select worklogs when parent task is selected
  useEffect(() => {
    if (selectedTasks[task.id]) {
      // If any child is already selected and we're not in select-all mode, skip auto-selecting
      const existingSelectedCount = Object.values(selected).filter(Boolean).length
      if (existingSelectedCount > 0 && !selectAllMode) {
        return
      }

      const newSelected: Record<string, boolean> = {}
      worklogs.forEach((log) => {
        newSelected[log.id] = true
        toggleWorklog(log.id, true)
      })
      setSelected(newSelected)
    } else {
      // Parent task was deselected, clear all worklogs for this task
      setSelected({})
      worklogs.forEach((log) => {
        toggleWorklog(log.id, false)
      })
    }
  }, [selectedTasks[task.id], worklogs.length, selectAllMode])

  // Reset selectAllMode after it's been processed
  useEffect(() => {
    if (selectAllMode) {
      const timeout = setTimeout(() => setSelectAllMode(false), 0)
      return () => clearTimeout(timeout)
    }
  }, [selectAllMode, setSelectAllMode])

  // Uncheck parent task when all child worklogs are deselected
  useEffect(() => {
    const selectedCount = Object.values(selected).filter(Boolean).length
    if (selectedCount === 0 && selectedTasks[task.id]) {
      toggleTask(task.id, false)
    }
  }, [Object.values(selected).filter(Boolean).length])

  // Check parent task when all child worklogs are selected
  useEffect(() => {
    if (worklogs.length > 0) {
      const selectedCount = Object.values(selected).filter(Boolean).length
      if (selectedCount === worklogs.length && !selectedTasks[task.id]) {
        toggleTask(task.id, true)
      }
    }
  }, [Object.values(selected).filter(Boolean).length, worklogs.length])

  const toggle = (id: string, value?: boolean) => {
    setSelected((s) => {
      const newValue = typeof value === "boolean" ? value : !s[id]
      toggleWorklog(id, newValue)
      if (newValue) {
        // ensure parent task is checked when any child worklog is selected.
        // The auto-select effect will skip selecting all children because
        // at least one is already selected.
        toggleTask(task.id, true)
      }
      return { ...s, [id]: newValue }
    })
  }

  // Approval handled elsewhere; approve UI removed from worklog list

  return (
    <div className="p-6">
      <div className="mb-4">
        <h3 className="font-semibold text-base">Work Logs</h3>
      </div>

      

      {worklogsLoading ? (
        <div className="text-sm text-muted-foreground">Loading work logs...</div>
      ) : worklogsError ? (
        <div className="text-sm text-destructive">
          Error loading work logs: {String(worklogsError)}
        </div>
      ) : worklogs.length === 0 ? (
        <div className="text-sm text-muted-foreground">No work logs found</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm table-auto border-collapse">
            <thead>
              <tr className="text-left">
                <th className="p-2" />
                <th className="p-2">Date</th>
                <th className="p-2">Start</th>
                <th className="p-2">End</th>
                <th className="p-2">Amount</th>
                <th className="p-2">Status</th>
                <th className="p-2">Tags</th>
              </tr>
            </thead>
            <tbody>
              {worklogs.map((log) => (
                <tr key={log.id} className="even:bg-muted/5">
                  <td className="p-2 align-top">
                    <Checkbox
                      checked={!!selected[log.id]}
                      onCheckedChange={(v) => toggle(log.id, v as boolean)}
                      aria-label={`Select worklog ${log.id}`}
                    />
                  </td>
                  <td className="p-2 align-top font-medium">
                    {new Date(log.start_time).toLocaleDateString()}
                  </td>
                  <td className="p-2 align-top">
                    {new Date(log.start_time).toLocaleString()}
                  </td>
                  <td className="p-2 align-top">
                    {new Date(log.end_time).toLocaleString()}
                  </td>
                  <td className="p-2 align-top text-green-600 font-semibold">
                    {formatAmount(Number(log.amount))}
                  </td>
                  <td className="p-2 align-top">
                    <span className="text-xs">
                      {log.approved ? "✓ Approved" : "○ Pending"}
                      {log.payment_initiated && " • Payment"}
                      {log.paid && " • Paid"}
                    </span>
                  </td>
                  <td className="p-2 align-top">
                    <div className="flex gap-2 items-center">
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {extractTimezone(log.start_time)}
                      </span>
                      {log.approved && (
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                          Approved
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
