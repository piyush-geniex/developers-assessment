import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { BarChart3 } from "lucide-react"
import { useState } from "react"

import { WorklogsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { columns } from "@/components/Worklogs/columns"
import PendingItems from "@/components/Pending/PendingItems"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export const Route = createFileRoute("/_layout/worklogs")({
  component: Worklogs,
  head: () => ({
    meta: [{ title: "Worklogs - FastAPI Cloud" }],
  }),
})

function Worklogs() {
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [filters, setFilters] = useState<{ dateFrom?: string; dateTo?: string }>({})

  const { data, isLoading } = useQuery({
    queryKey: ["worklogs", filters],
    queryFn: () =>
      WorklogsService.readWorklogsSummary({
        dateFrom: filters.dateFrom || undefined,
        dateTo: filters.dateTo || undefined,
      }),
  })

  const handleApply = () => {
    setFilters({
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
    })
  }

  const handleClear = () => {
    setDateFrom("")
    setDateTo("")
    setFilters({})
  }

  const totalHours = data?.data.reduce((sum, row) => sum + row.total_hours, 0) ?? 0
  const totalAmount = data?.data.reduce((sum, row) => sum + row.total_amount, 0) ?? 0

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Worklogs</h1>
        <p className="text-muted-foreground">Aggregate summary of time entries by task</p>
      </div>

      <div className="flex flex-wrap items-end gap-4 rounded-lg border bg-card p-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="date-from">From</Label>
          <Input
            id="date-from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-40"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="date-to">To</Label>
          <Input
            id="date-to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-40"
          />
        </div>
        <div className="flex gap-2">
          <Button onClick={handleApply}>Apply</Button>
          {(filters.dateFrom || filters.dateTo) && (
            <Button variant="outline" onClick={handleClear}>Clear</Button>
          )}
        </div>
      </div>

      {(totalHours > 0 || totalAmount > 0) && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border bg-card p-4">
            <p className="text-sm text-muted-foreground">Total Entries</p>
            <p className="text-2xl font-bold tabular-nums">{data?.count ?? 0}</p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-sm text-muted-foreground">Total Hours</p>
            <p className="text-2xl font-bold tabular-nums">{totalHours.toFixed(2)}h</p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-sm text-muted-foreground">Total Amount</p>
            <p className="text-2xl font-bold tabular-nums">
              {totalAmount > 0 ? `$${totalAmount.toFixed(2)}` : "—"}
            </p>
          </div>
        </div>
      )}

      {isLoading ? (
        <PendingItems />
      ) : !data || data.data.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center py-12">
          <div className="rounded-full bg-muted p-4 mb-4">
            <BarChart3 className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">No worklog data</h3>
          <p className="text-muted-foreground">
            {filters.dateFrom || filters.dateTo
              ? "No entries found for the selected date range"
              : "Log time entries to see them here"}
          </p>
        </div>
      ) : (
        <DataTable columns={columns} data={data.data} />
      )}
    </div>
  )
}
