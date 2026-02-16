import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Clock, Filter } from "lucide-react"
import { Suspense, useState } from "react"

import { DataTable } from "@/components/Common/DataTable"
import { columns } from "@/components/Worklogs/columns"
import { WorklogsService } from "@/components/Worklogs/service"
import AddWorklog from "@/components/Worklogs/AddWorklog"
import PendingItems from "@/components/Pending/PendingItems"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import useCustomToast from "@/hooks/useCustomToast"

function getWorklogsQueryOptions(filters: { start_date?: string; end_date?: string }) {
  return {
    queryFn: () =>
      WorklogsService.readWorklogs({
        skip: 0,
        limit: 100,
        start_date: filters.start_date,
        end_date: filters.end_date,
      }),
    queryKey: ["worklogs", filters],
  }
}

export const Route = createFileRoute("/_layout/worklogs")({
  component: Worklogs,
  head: () => ({
    meta: [
      {
        title: "Worklogs - FastAPI Cloud",
      },
    ],
  }),
})

function WorklogsTableContent() {
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [appliedFilters, setAppliedFilters] = useState<{ start_date?: string; end_date?: string }>({})
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())

  const { data: worklogs } = useSuspenseQuery(getWorklogsQueryOptions(appliedFilters))
  const navigate = useNavigate()
  const { showErrorToast } = useCustomToast()

  const handleApplyFilters = () => {
    setAppliedFilters({
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    })
  }

  const handleClearFilters = () => {
    setStartDate("")
    setEndDate("")
    setAppliedFilters({})
  }

  const handleReviewPayment = () => {
    if (selectedRows.size === 0) {
      showErrorToast("Please select at least one worklog to process payment.")
      return
    }

    const selectedIds = Array.from(selectedRows)
    navigate({
      to: "/payment-review",
      search: { ids: selectedIds.join(",") },
    })
  }

  const toggleRowSelection = (id: number) => {
    const newSelection = new Set(selectedRows)
    if (newSelection.has(id)) {
      newSelection.delete(id)
    } else {
      newSelection.add(id)
    }
    setSelectedRows(newSelection)
  }

  const toggleAllRows = () => {
    if (selectedRows.size === worklogs.data.filter((w: any) => w.status === "PENDING").length) {
      setSelectedRows(new Set())
    } else {
      const allPendingIds = worklogs.data
        .filter((w: any) => w.status === "PENDING")
        .map((w: any) => w.id)
      setSelectedRows(new Set(allPendingIds))
    }
  }

  if (worklogs.data.length === 0 && Object.keys(appliedFilters).length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Clock className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No worklogs yet</h3>
        <p className="text-muted-foreground">Worklogs will appear here once created</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Date Filters */}
      <div className="flex items-end gap-4 p-4 rounded-lg border bg-card">
        <div className="flex-1">
          <label className="text-sm font-medium mb-2 block">Start Date</label>
          <Input
            type="date"
            value={startDate}
            onChange={(e: any) => setStartDate(e.target.value)}
          />
        </div>
        <div className="flex-1">
          <label className="text-sm font-medium mb-2 block">End Date</label>
          <Input
            type="date"
            value={endDate}
            onChange={(e: any) => setEndDate(e.target.value)}
          />
        </div>
        <Button onClick={handleApplyFilters}>
          <Filter className="h-4 w-4 mr-2" />
          Apply Filters
        </Button>
        {(appliedFilters.start_date || appliedFilters.end_date) && (
          <Button variant="outline" onClick={handleClearFilters}>
            Clear
          </Button>
        )}
      </div>

      {/* Selection Actions */}
      {selectedRows.size > 0 && (
        <div className="flex items-center justify-between p-4 rounded-lg border bg-muted">
          <span className="text-sm font-medium">
            {selectedRows.size} worklog{selectedRows.size !== 1 ? "s" : ""} selected
          </span>
          <Button onClick={handleReviewPayment}>
            Review Payment
          </Button>
        </div>
      )}

      {/* Data Table with Extended Columns */}
      <DataTable
        columns={[
          {
            id: "select",
            header: () => (
              <input
                type="checkbox"
                checked={
                  worklogs.data.filter((w: any) => w.status === "PENDING").length > 0 &&
                  selectedRows.size === worklogs.data.filter((w: any) => w.status === "PENDING").length
                }
                onChange={toggleAllRows}
                className="cursor-pointer"
              />
            ),
            cell: ({ row }: any) =>
              row.original.status === "PENDING" ? (
                <input
                  type="checkbox"
                  checked={selectedRows.has(row.original.id)}
                  onChange={() => toggleRowSelection(row.original.id)}
                  className="cursor-pointer"
                />
              ) : null,
          },
          ...columns,
        ]}
        data={worklogs.data}
      />

      {worklogs.data.length === 0 && Object.keys(appliedFilters).length > 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No worklogs found for the selected date range
        </div>
      )}
    </div>
  )
}

function WorklogsTable() {
  return (
    <Suspense fallback={<PendingItems />}>
      <WorklogsTableContent />
    </Suspense>
  )
}

function Worklogs() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Work Logs</h1>
          <p className="text-muted-foreground">View and manage freelancer work logs</p>
        </div>
        <AddWorklog />
      </div>
      <WorklogsTable />
    </div>
  )
}
