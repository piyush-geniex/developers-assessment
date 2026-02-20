import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Search } from "lucide-react"
import { Suspense, useState } from "react"

import { TasksService, WorkLogEntryBulkDelete, WorkLogEntryBulkPaymentInitiate } from "@/client"
import { ExpandableDataTable } from "@/components/Common/ExpandableDataTable"
import AddTask from "@/components/Tasks/AddTask"
import { ActionBar } from "@/components/Tasks/ActionBar"
import { TaskExpansionContext } from "@/components/Tasks/TaskExpansionContext"
import { TaskSelectionContext } from "@/components/Tasks/TaskSelectionContext"
import { DateFilter } from "@/components/Tasks/DateFilter"
import { columns } from "@/components/Tasks/columns"
import { TaskWorkLogsSubComponent } from "@/components/Tasks/TaskWorkLogsSubComponent"
import PendingTasks from "@/components/Pending/PendingTasks"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

function getTasksQueryOptions(startDate?: string | null, endDate?: string | null) {
  return {
    queryFn: () =>
      TasksService.readTasks({
        skip: 0,
        limit: 100,
        startDate: startDate ? new Date(startDate).toISOString() : undefined,
        endDate: endDate ? new Date(endDate).toISOString() : undefined,
      }),
    queryKey: ["tasks", startDate, endDate],
  }
}

export const Route = createFileRoute("/_layout/tasks")({
  component: Tasks,
  head: () => ({
    meta: [
      {
        title: "Tasks - FastAPI Cloud",
      },
    ],
  }),
})

function TasksTableContent({
  expandedRows,
  startDate,
  endDate,
  onSelectAll,
  onSelectNone,
  onDeleteSelected,
  onPaySelected,
}: {
  expandedRows: Set<string>
  startDate: string | null
  endDate: string | null
  onSelectAll: (taskIds: string[]) => void
  onSelectNone: () => void
  onDeleteSelected: () => void
  onPaySelected: () => void
}) {
  const { data: tasks } = useSuspenseQuery(
    getTasksQueryOptions(startDate, endDate)
  )

  if (tasks.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">You don't have any tasks yet</h3>
        <p className="text-muted-foreground">Add a new task to get started</p>
      </div>
    )
  }

  const handleSelectAllClick = () => {
    onSelectAll(tasks.data.map((t) => t.id))
  }

  return (
    <div>
      <ActionBar
        tasks={tasks.data}
        onSelectAll={handleSelectAllClick}
        onSelectNone={onSelectNone}
        onDeleteSelected={onDeleteSelected}
        onPaySelected={onPaySelected}
      />
      <ExpandableDataTable
        columns={columns}
        data={tasks.data}
        renderSubComponent={(task) => (
          <TaskWorkLogsSubComponent task={task} />
        )}
        expandedRows={expandedRows}
      />
    </div>
  )
}

function TasksTable({
  startDate,
  endDate,
}: {
  startDate: string | null
  endDate: string | null
}) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [selectedTasks, setSelectedTasks] = useState<Record<string, boolean>>({})
  const [selectedWorklogs, setSelectedWorklogs] = useState<Record<string, boolean>>({})
  const [selectAllMode, setSelectAllMode] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const queryClient = useQueryClient()
  const handleToggleRow = (rowId: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(rowId)) {
      newExpanded.delete(rowId)
    } else {
      newExpanded.add(rowId)
    }
    setExpandedRows(newExpanded)
  }

  const toggleTask = (taskId: string, value?: boolean) => {
    const isSelected = typeof value === "boolean" ? value : !selectedTasks[taskId]
    setSelectedTasks((s) => ({ ...s, [taskId]: isSelected }))
  }

  const toggleWorklog = (worklogId: string, value?: boolean) => {
    setSelectedWorklogs((s) => ({
      ...s,
      [worklogId]: typeof value === "boolean" ? value : !s[worklogId],
    }))
  }

  const handleSelectAll = (taskIds: string[]) => {
    const newSelected: Record<string, boolean> = {}
    taskIds.forEach((id) => {
      newSelected[id] = true
    })
    setSelectedTasks(newSelected)
    setSelectAllMode(true)
  }

  const handleSelectNone = () => {
    setSelectedTasks({})
    setSelectedWorklogs({})
  }

    const deletedMutation = useMutation({
        mutationFn: (data: WorkLogEntryBulkDelete) =>
        TasksService.bulkDelete({requestBody: { entry_ids: data.entry_ids }}),
        onSuccess: () => {
        showSuccessToast("Work log entry deleted successfully")
        setSelectedTasks({})
        setSelectedWorklogs({})
        setExpandedRows(new Set())
        },
        onError: handleError.bind(showErrorToast),
        onSettled: () => {
        queryClient.invalidateQueries({ queryKey: ["worklogs"] })
        queryClient.invalidateQueries({ queryKey: ["tasks"] })
        },
    })

        const paidMutation = useMutation({
        mutationFn: (data: WorkLogEntryBulkPaymentInitiate) =>
        TasksService.initiatePayments({requestBody: { entry_ids: data.entry_ids }}),
        onSuccess: () => {
        showSuccessToast("Work logs payment initiated successfully")
        setSelectedTasks({})
        setSelectedWorklogs({})
        setExpandedRows(new Set())
        },
        onError: handleError.bind(showErrorToast),
        onSettled: () => {
        queryClient.invalidateQueries({ queryKey: ["worklogs"] })
        queryClient.invalidateQueries({ queryKey: ["tasks"] })
        },
    })

  const handleDeleteSelected = async () => {
    const entryIdsToDelete = Object.keys(selectedWorklogs).filter((id) => selectedWorklogs[id])
    deletedMutation.mutate({ entry_ids: entryIdsToDelete })
    console.log("Delete selected:", { selectedWorklogs })
  }

  const handlePaySelected = () => {
    const entryIdsToPay = Object.keys(selectedWorklogs).filter((id) => selectedWorklogs[id])
    paidMutation.mutate({entry_ids: entryIdsToPay})
    console.log("Pay selected:", { selectedWorklogs })
  }

  return (
    <TaskExpansionContext.Provider value={{ expandedRows, onToggleRow: handleToggleRow }}>
      <TaskSelectionContext.Provider
        value={{
          selectedTasks,
          toggleTask,
          selectedWorklogs,
          toggleWorklog,
          selectAllMode,
          setSelectAllMode,
        }}
      >
        <Suspense fallback={<PendingTasks />}>
          <TasksTableContent
            expandedRows={expandedRows}
            startDate={startDate}
            endDate={endDate}
            onSelectAll={handleSelectAll}
            onSelectNone={handleSelectNone}
            onDeleteSelected={handleDeleteSelected}
            onPaySelected={handlePaySelected}
          />
        </Suspense>
      </TaskSelectionContext.Provider>
    </TaskExpansionContext.Provider>
  )
}

function Tasks() {
  const [inputStartDate, setInputStartDate] = useState<string | null>(null)
  const [inputEndDate, setInputEndDate] = useState<string | null>(null)
  const [appliedStartDate, setAppliedStartDate] = useState<string | null>(null)
  const [appliedEndDate, setAppliedEndDate] = useState<string | null>(null)

  const handleResetFilter = () => {
    setInputStartDate(null)
    setInputEndDate(null)
    setAppliedStartDate(null)
    setAppliedEndDate(null)
  }

  const handleSearch = () => {
    setAppliedStartDate(inputStartDate)
    setAppliedEndDate(inputEndDate)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tasks</h1>
          <p className="text-muted-foreground">View and manage your tasks</p>
        </div>
          <DateFilter
            startDate={inputStartDate}
            endDate={inputEndDate}
            onStartDateChange={setInputStartDate}
            onEndDateChange={setInputEndDate}
            onReset={handleResetFilter}
            onSearch={handleSearch}
          />
          <AddTask />
      </div>
      <TasksTable startDate={appliedStartDate} endDate={appliedEndDate} />
    </div>
  )
}

