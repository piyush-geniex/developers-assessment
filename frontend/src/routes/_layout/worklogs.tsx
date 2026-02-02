import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, Outlet, useRouterState } from "@tanstack/react-router"
import { Calendar, Search } from "lucide-react"
import { useEffect, useState } from "react"

import {
  type WorkLogListItem,
  type WorkLogRemittanceFilter,
  WorklogsService,
} from "@/api/worklogs"
import { ApiError } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import PendingItems from "@/components/Pending/PendingItems"

function getWorklogsQueryOptions(params: {
  date_from?: string
  date_to?: string
  remittance_status?: WorkLogRemittanceFilter | null
}) {
  return {
    queryKey: ["worklogs", params],
    queryFn: () =>
      WorklogsService.listWorklogs({
        skip: 0,
        limit: 500,
        date_from: params.date_from || undefined,
        date_to: params.date_to || undefined,
        remittance_status: params.remittance_status ?? undefined,
      }),
  }
}

const worklogColumns = [
  {
    accessorKey: "task_title" as const,
    header: "Task",
    cell: ({ row }: { row: { original: WorkLogListItem } }) => (
      <span className="font-medium">{row.original.task_title}</span>
    ),
  },
  {
    accessorKey: "user_email" as const,
    header: "Freelancer",
    cell: ({ row }: { row: { original: WorkLogListItem } }) => (
      <span>
        {row.original.user_full_name || row.original.user_email}
      </span>
    ),
  },
  {
    accessorKey: "amount_cents" as const,
    header: "Earned",
    cell: ({ row }: { row: { original: WorkLogListItem } }) =>
      `$${(row.original.amount_cents / 100).toFixed(2)}`,
  },
  {
    accessorKey: "remittance_status" as const,
    header: "Status",
    cell: ({ row }: { row: { original: WorkLogListItem } }) => (
      <span
        className={
          row.original.remittance_id
            ? "text-muted-foreground"
            : "text-green-600 dark:text-green-400"
        }
      >
        {row.original.remittance_id ? "Paid" : "Unpaid"}
      </span>
    ),
  },
  {
    id: "actions" as const,
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }: { row: { original: WorkLogListItem } }) => (
      <Button variant="ghost" size="sm" asChild>
        <Link
          to="/worklogs/$workLogId"
          params={{ workLogId: String(row.original.id) }}
          search={{ date_from: "", date_to: "", remittance_status: "" }}
        >
          View entries
        </Link>
      </Button>
    ),
  },
]

function WorklogsTableContent({
  dateFrom,
  dateTo,
  remittanceStatus,
}: {
  dateFrom: string
  dateTo: string
  remittanceStatus: WorkLogRemittanceFilter | "" | null
}) {
  const navigate = Route.useNavigate()
  const { data, isPending, isError, error } = useQuery(
    getWorklogsQueryOptions({
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      remittance_status:
        remittanceStatus === "" || remittanceStatus === null
          ? undefined
          : remittanceStatus,
    }),
  )

  // On 401/403, redirect to dashboard instead of showing error (user stays logged in)
  useEffect(() => {
    if (
      isError &&
      error instanceof ApiError &&
      (error.status === 401 || error.status === 403)
    ) {
      navigate({ to: "/" })
    }
  }, [isError, error, navigate])

  if (isPending) {
    return <PendingItems />
  }

  if (isError) {
    const isAuthError =
      error instanceof ApiError && (error.status === 401 || error.status === 403)
    if (isAuthError) {
      return <PendingItems />
    }
    const message =
      error instanceof Error ? error.message : "Failed to load worklogs."
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-destructive/50 bg-destructive/10 py-12 text-center">
        <p className="font-medium text-destructive">Error loading worklogs</p>
        <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      </div>
    )
  }

  if (!data || data.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="mb-4 rounded-full bg-muted p-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No worklogs found</h3>
        <p className="text-muted-foreground">
          Try adjusting the date range or status filter
        </p>
      </div>
    )
  }

  return <DataTable columns={worklogColumns} data={data.data} />
}

function WorklogsTable({
  dateFrom,
  dateTo,
  remittanceStatus,
}: {
  dateFrom: string
  dateTo: string
  remittanceStatus: WorkLogRemittanceFilter | "" | null
}) {
  return (
    <WorklogsTableContent
      dateFrom={dateFrom}
      dateTo={dateTo}
      remittanceStatus={remittanceStatus}
    />
  )
}

type WorklogsSearch = {
  date_from: string
  date_to: string
  remittance_status: "" | WorkLogRemittanceFilter
}

export const Route = createFileRoute("/_layout/worklogs")({
  component: WorklogsPage,
  validateSearch: (search: Record<string, unknown>): WorklogsSearch => ({
    date_from: (search.date_from as string) || "",
    date_to: (search.date_to as string) || "",
    remittance_status:
      (search.remittance_status as WorkLogRemittanceFilter | "" | undefined) ||
      "",
  }),
  head: () => ({
    meta: [{ title: "WorkLogs - Payment Dashboard" }],
  }),
})

function WorklogsPage() {
  const { date_from, date_to, remittance_status } = Route.useSearch()
  const navigate = Route.useNavigate()
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const [dateFrom, setDateFrom] = useState(date_from)
  const [dateTo, setDateTo] = useState(date_to)
  const [statusFilter, setStatusFilter] = useState<
    "" | WorkLogRemittanceFilter | null
  >(remittance_status === "" ? null : remittance_status)

  // Show detail child when path is /worklogs/:id
  const isDetailView =
    pathname !== "/worklogs" && pathname.startsWith("/worklogs/")

  useEffect(() => {
    setDateFrom(date_from)
    setDateTo(date_to)
    setStatusFilter(remittance_status === "" ? null : remittance_status)
  }, [date_from, date_to, remittance_status])

  const applyFilters = () => {
    navigate({
      to: "/worklogs",
      search: {
        date_from: dateFrom || "",
        date_to: dateTo || "",
        remittance_status: statusFilter ?? "",
      },
    })
  }

  if (isDetailView) {
    return <Outlet />
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">WorkLogs</h1>
        <p className="text-muted-foreground">
          View all worklogs and earnings per task. Drill down to see time
          entries.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4 rounded-lg border p-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="date_from">From date</Label>
          <div className="relative">
            <Calendar className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="date_from"
              type="date"
              className="pl-8"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="date_to">To date</Label>
          <Input
            id="date_to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label>Status</Label>
          <Select
            value={statusFilter ?? "all"}
            onValueChange={(v: string) =>
              setStatusFilter(
                v === "all" ? null : (v as WorkLogRemittanceFilter),
              )
            }
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="UNREMITTED">Unpaid</SelectItem>
              <SelectItem value="REMITTED">Paid</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button onClick={applyFilters}>Apply filters</Button>
      </div>

      <WorklogsTable
        dateFrom={date_from || dateFrom}
        dateTo={date_to || dateTo}
        remittanceStatus={
          statusFilter ?? (remittance_status === "" ? null : remittance_status)
        }
      />
    </div>
  )
}
