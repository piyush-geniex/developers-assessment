import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { FileText } from "lucide-react"
import { Suspense, useState } from "react"

import { WorklogsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { columns } from "@/components/Worklogs/columns"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"

function getWorklogsQueryOptions(dateFrom: string, dateTo: string) {
  return {
    queryKey: ["worklogs", { dateFrom, dateTo }],
    queryFn: () =>
      WorklogsService.readWorklogs({
        limit: 200,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
      }),
  }
}

export const Route = createFileRoute("/_layout/worklogs")({
  component: Worklogs,
  head: () => ({
    meta: [{ title: "Worklogs - WorkLog Dashboard" }],
  }),
})

function WorklogsTableSkeleton() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Worklog</TableHead>
          <TableHead>Freelancer</TableHead>
          <TableHead>Rate</TableHead>
          <TableHead>Hours</TableHead>
          <TableHead>Earned</TableHead>
          <TableHead><span className="sr-only">Actions</span></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: 8 }).map((_, i) => (
          <TableRow key={i}>
            <TableCell><Skeleton className="h-4 w-40" /></TableCell>
            <TableCell><Skeleton className="h-4 w-28" /></TableCell>
            <TableCell><Skeleton className="h-4 w-16" /></TableCell>
            <TableCell><Skeleton className="h-4 w-16" /></TableCell>
            <TableCell><Skeleton className="h-4 w-20" /></TableCell>
            <TableCell><Skeleton className="size-8 rounded-md ml-auto" /></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

function WorklogsTableContent({
  dateFrom,
  dateTo,
}: {
  dateFrom: string
  dateTo: string
}) {
  const { data } = useSuspenseQuery(getWorklogsQueryOptions(dateFrom, dateTo))

  if (data.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-16">
        <div className="rounded-full bg-muted p-4 mb-4">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No worklogs found</h3>
        <p className="text-muted-foreground text-sm mt-1">
          {dateFrom || dateTo
            ? "No worklogs have time entries in the selected date range."
            : "No worklogs have been created yet."}
        </p>
      </div>
    )
  }

  return <DataTable columns={columns} data={data.data} />
}

function WorklogsTable({
  dateFrom,
  dateTo,
}: {
  dateFrom: string
  dateTo: string
}) {
  return (
    <Suspense fallback={<WorklogsTableSkeleton />}>
      <WorklogsTableContent dateFrom={dateFrom} dateTo={dateTo} />
    </Suspense>
  )
}

function Worklogs() {
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")

  function handleClearFilter() {
    setDateFrom("")
    setDateTo("")
  }

  const hasFilter = dateFrom || dateTo

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Worklogs</h1>
          <p className="text-muted-foreground text-sm mt-0.5">
            Review time logged by freelancers and their earnings.
          </p>
        </div>
      </div>

      <div className="flex items-end gap-4 p-4 bg-muted/40 rounded-lg border">
        <div className="grid gap-1.5">
          <Label htmlFor="date-from">From</Label>
          <Input
            id="date-from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-44"
            aria-label="Filter start date"
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="date-to">To</Label>
          <Input
            id="date-to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-44"
            aria-label="Filter end date"
          />
        </div>
        {hasFilter && (
          <Button
            variant="ghost"
            onClick={handleClearFilter}
            aria-label="Clear date filter"
          >
            Clear filter
          </Button>
        )}
      </div>

      <WorklogsTable dateFrom={dateFrom} dateTo={dateTo} />
    </div>
  )
}
